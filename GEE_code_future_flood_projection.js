// =============================================================================
// Flood Duration Future Projection using Random Forest Model
// -----------------------------------------------------------------------------
// Trains a Random Forest regression model on historical CMIP6 climate variables
// and observed flood duration (GFD), then predicts future flood exposure
// under SSP126, SSP245, and SSP585 scenarios from 2020 to 2100.
// =============================================================================


// === User Settings ===
var geometry = 
    ee.Geometry.Polygon(
        [[[-179.59378509521488, 89.94991764178175],
          [-179.59378509521488, -89.96339812345498],
          [180.40209503173824, -89.96339812345498],
          [180.40209503173824, 89.94991764178175]]], null, false);
          
var AOI = geometry;  // Study area geometry
var models = ['CanESM5', 'CNRM-ESM2-1', 'GFDL-ESM4', 'MPI-ESM1-2-LR', 'UKESM1-0-LL'];
var modelName = models[0];  // Change index to run for different GCMs
print(modelName);

var scenarios = ['ssp126', 'ssp245', 'ssp585'];
var startYear = 2000;
var endYear = 2014;
var futureStart = 2020;
var futureEnd = 2100;
var targetScale = 27830;  // Output resolution in meters (approx. CMIP6 native resolution)
var varList = ['tasmax', 'tasmin', 'tas', 'pr', 'hurs', 'huss', 'rsds', 'rlds'];


// =============================================================================
// Step 0: Compute Annual Flood Duration from GFD and Export to Asset
// =============================================================================
// Global Flood Database (GFD): binary daily flood events aggregated to annual duration.
// JRC Global Surface Water transition layer is used to mask permanent water bodies.

var gfd = ee.ImageCollection("GLOBAL_FLOOD_DB/MODIS_EVENTS/V1");
var jrc = ee.Image("JRC/GSW1_4/GlobalSurfaceWater").select('transition');

var floodImage = ee.Image([]);
for (var year = startYear; year <= 2018; year++) {
  var floodyear = gfd.filterDate(year + '-01-01', year + '-12-31')
                     .select('duration')
                     .sum()
                     .updateMask(jrc.neq(1))  // Exclude permanent water (transition class 1)
                     .rename('duration_' + year)
                     .setDefaultProjection('EPSG:4326', null, 250);
  floodImage = floodImage.addBands(floodyear);

  if (year == endYear) {
    Map.addLayer(floodyear, {min: 0, max: 3, palette: ['black', '#deebf7', '#9ecae1', '#08519c']}, 'floodyear-' + year, false);
  }
}
print('floodImage', floodImage);

/*
// Export annual flood duration stack (2000–2018) to GEE Asset
Export.image.toAsset({
  image: floodImage,
  description: 'GFD_duration_250m_2000_2018',
  assetId: 'projects/ee-thutyecology/assets/Hazard/GFD_duration_250m_2000_2018',
  region: AOI,
  scale: 250,
  crs: 'EPSG:4326',
  maxPixels: 1e13
});
*/

// Instead, load pre-exported flood duration asset.
var floodImage = ee.Image("projects/ee-thutyecology/assets/Hazard/GFD_duration_250m_2000_2018");
Map.addLayer(floodImage.select('duration_2000'), {min: 0, max: 3, palette: ['black', 'blue', 'yellow', 'red']}, 'duration-2000', false);
Map.addLayer(floodImage.select('duration_2014'), {min: 0, max: 3, palette: ['black', 'blue', 'yellow', 'red']}, 'duration-2014', false);

// =============================================================================
// Step 1: Compute Multi-Year Mean Flood Duration (Training Label)
// =============================================================================

// Compute mean flood duration over the historical period (2000–2014)
var floodMean = floodImage.select(
  ee.List.sequence(startYear, endYear).map(function(i) {
    return ee.String('duration_').cat(ee.Number(i).int());
  })
).reduce(ee.Reducer.mean()).rename('duration');

// Load extreme heat data to define land mask (Tuholske et al., 2021)
var hwdImgRaw = ee.Image("projects/ee-thutyecology/assets/Hazard/wbgtmax30_count_merge");

// Mask ocean; fill non-flooded land pixels with 0
var floodMeanMask = floodMean
  .updateMask(floodMean.gt(0))
  .unmask(0)
  .mask(hwdImgRaw.select('b32').mask());

// Reproject flood image to match CMIP6 resolution
var floodMeanMaskPrj = floodMeanMask
  .resample('bilinear')
  .reproject({crs: 'EPSG:4326', scale: targetScale});

Map.addLayer(floodMeanMask,    {min: 0, max: 3, palette: ['black', 'blue', 'yellow', 'red']}, 'floodMeanMask');
Map.addLayer(floodMeanMaskPrj, {min: 0, max: 3, palette: ['black', 'blue', 'yellow', 'red']}, 'floodMeanMaskPrj');


// =============================================================================
// Step 2: Compute Multi-Year Mean CMIP6 Climate Variables (Training Features)
// =============================================================================
// For each variable in varList, compute the daily mean within each year,
// then average across all years to obtain a single multi-year mean image.

function getMeanVars(startYear, endYear, experiment) {
  var years = ee.List.sequence(startYear, endYear);
  var imageList = [];

  for (var i = 0; i < varList.length; i++) {
    var varName = varList[i];
    var yearlyList = [];

    for (var j = 0; j < years.length().getInfo(); j++) {
      var y = ee.Number(years.get(j));

      var ic = ee.ImageCollection("NASA/GDDP-CMIP6")
        .filter(ee.Filter.eq('model', modelName))
        .filter(ee.Filter.eq('scenario', experiment))
        .filter(ee.Filter.eq('year', y))
        .select([varName]);

      var img = ic.mean().rename(varName);
      yearlyList.push(ee.Image(img));
    }

    // Average the annual means across all years
    var varMean = ee.ImageCollection(yearlyList).mean().rename(varName);
    imageList.push(varMean);
  }

  return ee.ImageCollection(imageList).toBands().rename(varList);
}

// Compute historical mean climate variables over 2000–2014
var cmipMean = getMeanVars(startYear, endYear, 'historical');


// =============================================================================
// Step 3: Assemble Training Image (Features + Label)
// =============================================================================

var fullImage = ee.Image(cmipMean.toFloat().addBands(floodMeanMaskPrj.toFloat()));


// =============================================================================
// Step 4: Sample Training Points
// =============================================================================
// ~3,000 points randomly distributed worldwide with a minimum spacing of 30 km
// to reduce spatial autocorrelation (pre-generated asset).

var points = ee.FeatureCollection("projects/ee-thutyecology/assets/Hazard/random_points_world_3k");
var trainingSamples = fullImage.sampleRegions({
  collection: points,
  scale: targetScale,
  geometries: true
});

Map.addLayer(points, {color: 'blue'}, 'Samples', false);
Map.addLayer(trainingSamples, {color: 'red'}, 'Valid Samples', false);
print('Valid training samples', trainingSamples.size());

// =============================================================================
// Step 5: Train Random Forest Regression Model
// =============================================================================

var regressor = ee.Classifier.smileRandomForest(1000)
  .setOutputMode('REGRESSION')
  .train({
    features: trainingSamples,
    classProperty: 'duration',
    inputProperties: varList
  });


// =============================================================================
// Step 6: Model Evaluation (R², MAE, RMSE on training samples)
// =============================================================================
// Uncomment evaluation() call below to run evaluation.

var predicted = trainingSamples.classify(regressor);
/*
Export.table.toDrive({
  collection: predicted,
  description: 'future_flood_rf_samples_' + modelName,
  fileFormat: 'CSV',
  fileNamePrefix: 'future_flood_rf_samples_' + modelName,
  folder: 'GEE-Hazard',
});
*/

function evaluation() {
  // Variable importance
  var importance = ee.Dictionary(regressor.explain().get('importance'));
  print('Variable importance', importance);

  // Compute error metrics
  var evaluated = predicted.map(function(f) {
    var trueValue = f.getNumber('duration');
    var predValue = f.getNumber('classification');
    var error = predValue.subtract(trueValue);
    return f.set({
      predicted: predValue,
      error:     error,
      absError:  error.abs(),
      sqError:   error.pow(2)
    });
  });

  var n    = evaluated.size();
  var mae  = evaluated.aggregate_mean('absError');
  var rmse = evaluated.aggregate_mean('sqError').sqrt();

  // Compute R² manually from covariance: R² = r²
  var statsHWD  = evaluated.aggregate_stats('duration');
  var statsPred = evaluated.aggregate_stats('predicted');
  var meanX = statsHWD.get('mean');
  var meanY = statsPred.get('mean');

  var covXY = evaluated.aggregate_array('duration')
    .zip(evaluated.aggregate_array('predicted'))
    .map(function(pair) {
      pair = ee.List(pair);
      return ee.Number(pair.get(0)).subtract(meanX)
        .multiply(ee.Number(pair.get(1)).subtract(meanY));
    }).reduce(ee.Reducer.sum());

  var varX = statsHWD.get('sample_sd');
  var varY = statsPred.get('sample_sd');
  var n    = evaluated.size();

  var r  = ee.Number(covXY).divide(n.multiply(varX).multiply(varY));
  var r2 = r.pow(2);

  print('MAE',  mae);
  print('RMSE', rmse);
  print('R2',   r2);
}
// evaluation();


// =============================================================================
// Step 7: Predict Historical Annual Flood Duration (2000–2014)
// =============================================================================

var histImage = ee.Image([]);

for (var i = 2000; i < 2015; i++) {
  var y    = ee.Number(i).toInt();
  var year = y.format();

  var annualVars = getMeanVars(y, y, 'historical');
  var prediction = annualVars.classify(regressor)
    .rename(ee.String('duration_').cat(year))
    .set('year', y);

  histImage = histImage.addBands(prediction);
}

print('Historical prediction image-' + modelName, histImage);

Export.image.toAsset({
  image:       histImage,
  description: 'flood_duration_historical_2000_2014_' + modelName,
  assetId:     'projects/{change to your assets name}/flood_duration_historical_2000_2014_' + modelName,
  region:      AOI,
  scale:       targetScale,
  crs:         'EPSG:4326',
  maxPixels:   1e13
});

Map.addLayer(histImage.select('duration_2000'), {min: 0, max: 3, palette: ['black', 'blue', 'yellow', 'red']}, 'Predicted 2000', false);
Map.addLayer(histImage.select('duration_2014'), {min: 0, max: 3, palette: ['black', 'blue', 'yellow', 'red']}, 'Predicted 2014', false);


// =============================================================================
// Step 8: Predict Future Annual Flood Duration (2020–2100, decadal)
// =============================================================================
// SSP126 is not available in NASA/GDDP-CMIP6; a pre-exported image asset is
// used instead. SSP245 and SSP585 are queried directly from the collection.

// Helper function: retrieve band names for a given year from the SSP126 band index asset
function getBandsByYear(bandIndex, year, variables) {
  var yearStr   = ee.Number(year).format();
  var bandNames = variables.map(function(v) {
    return ee.String(v).cat('_').cat(yearStr);
  });

  return bandIndex
    .filter(ee.Filter.inList('name', bandNames))
    .sort('band')  // Ensure consistent band order
    .aggregate_array('band')
    .map(function(i) {
      return ee.String('b').cat(ee.Number(i).format());
    });
}

// Load pre-exported SSP126 CMIP6 image and its band index
var band_index  = ee.FeatureCollection("projects/ee-thutyecology/assets/Hazard/ssp126_2020_2100_band_index");
var cmip6_image = ee.Image("projects/ee-thutyecology/assets/Hazard/ssp126_2020_2100_" + modelName)
  .resample('bilinear')
  .reproject({crs: 'EPSG:4326', scale: targetScale});

// Loop over all three SSP scenarios
for (var j = 0; j < 3; j++) {
  var scenario    = scenarios[j];
  var futureYears = ee.List.sequence(futureStart, futureEnd);
  var futureImage = ee.Image([]);

  // Predict at decadal intervals (2020, 2030, ..., 2100)
  for (var i = 0; i < futureYears.length().getInfo(); i += 10) {
    var y    = ee.Number(futureYears.get(i)).toInt();
    var year = y.format();

    if (scenario == 'ssp126') {
      // SSP126 is not available in NASA/GDDP-CMIP6; use pre-exported image asset instead
      var bandNames  = getBandsByYear(band_index, y, varList);
      var annualVars = cmip6_image.select(bandNames).rename(varList);
    } else {
      var annualVars = getMeanVars(y, y, scenario);
    }

    var prediction = annualVars.classify(regressor)
      .rename(ee.String('duration_').cat(year))
      .set('year', y);

    futureImage = futureImage.addBands(prediction);
  }

  print('Future prediction image ' + scenario, futureImage);

  Export.image.toAsset({
    image:       futureImage,
    description: 'flood_duration_predicted_' + futureStart + '_' + futureEnd + '_' + modelName + '_' + scenario,
    assetId:     'projects/{change to your assets name}/flood_duration_predicted_' + futureStart + '_' + futureEnd + '_' + modelName + '_' + scenario,
    region:      AOI,
    scale:       targetScale,
    crs:         'EPSG:4326',
    maxPixels:   1e13
  });
}

Map.addLayer(futureImage.select('duration_2020'), {min: 0, max: 3, palette: ['black', 'blue', 'yellow', 'red']}, 'Predicted 2020', false);
Map.addLayer(futureImage.select('duration_2050'), {min: 0, max: 3, palette: ['black', 'blue', 'yellow', 'red']}, 'Predicted 2050');
Map.addLayer(futureImage.select('duration_2070'), {min: 0, max: 3, palette: ['black', 'blue', 'yellow', 'red']}, 'Predicted 2070', false);