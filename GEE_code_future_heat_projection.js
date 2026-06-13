// =============================================================================
// Extreme Heat Days Future Projection using Random Forest Model
// -----------------------------------------------------------------------------
// Trains a Random Forest regression model on historical CMIP6 climate variables
// and observed extreme heat days (GEHE/WBGTmax > 30°C), then predicts future
// heat exposure under SSP126, SSP245, and SSP585 scenarios from 2020 to 2100.
// =============================================================================


// === User Settings ===
var geometry = ee.Geometry.Polygon(
        [[[-179.59378509521488, 89.94991764178175],
          [-179.59378509521488, -89.96339812345498],
          [180.40209503173824, -89.96339812345498],
          [180.40209503173824, 89.94991764178175]]], null, false);

var AOI = geometry;  // Study area (global extent)
var models = ['CanESM5', 'CNRM-ESM2-1', 'GFDL-ESM4', 'MPI-ESM1-2-LR', 'UKESM1-0-LL'];
var modelName = models[0];  // Change index to run for different GCMs
print(modelName);

var scenarios = ['ssp126', 'ssp245', 'ssp585'];
var startYear = 1983;  // Heat historical period: 1983–2014 (matching GEHE dataset coverage)
var endYear = 2014;
var futureStart = 2020;
var futureEnd = 2100;
var targetScale = 27830;  // Output resolution in meters (approx. CMIP6 native resolution)
var varList = ['tasmax', 'tasmin', 'tas', 'pr', 'hurs', 'huss', 'rsds', 'rlds'];


// =============================================================================
// Step 1: Compute Multi-Year Mean Extreme Heat Days (Training Label)
// =============================================================================
// Source: Tuholske et al. (2021) global extreme heat exposure dataset (GEHE),
// based on WBGTmax > 30°C threshold at 0.05° resolution.
// Band index: b1 = 1983, b2 = 1984, ..., b32 = 2014, b33 = 2015, b34 = 2016.
// We use b1–b32 to match the historical period 1983–2014.

var hwdImgRaw = ee.Image("projects/ee-thutyecology/assets/Hazard/wbgtmax30_count_merge");

// Resample to CMIP6 resolution for alignment with explanatory variables
var hwdImg = hwdImgRaw
  .resample('bilinear')
  .reproject({crs: 'EPSG:4326', scale: targetScale});

Map.addLayer(hwdImgRaw.select('b32'), {min: 0, max: 50}, 'hwdImgRaw-2014', false);
Map.addLayer(hwdImg.select('b32'), {min: 0, max: 50}, 'hwdImg-2014', false);

// Compute mean annual extreme heat days over 1983–2014 (bands b1–b32)
var hwdMean = hwdImg.select(
  ee.List.sequence(1, 32).map(function(i) {
    return ee.String('b').cat(ee.Number(i).int());
  })
).reduce(ee.Reducer.mean()).rename('HWD');


// =============================================================================
// Step 2: Compute Multi-Year Mean CMIP6 Climate Variables (Training Features)
// =============================================================================
// For each variable in varList, compute the daily mean within each year,
// then average across all years to obtain a single multi-year mean image.
// Historical period: 1983–2014, matching the GEHE training label.

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

// Compute historical mean climate variables over 1983–2014
var cmipMean = getMeanVars(startYear, endYear, 'historical');


// =============================================================================
// Step 3: Assemble Training Image (Features + Label)
// =============================================================================

var fullImage = ee.Image(cmipMean.addBands(hwdMean)).toFloat();


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
    classProperty: 'HWD',
    inputProperties: varList
  });


// =============================================================================
// Step 6: Model Evaluation (R², MAE, RMSE on training samples)
// =============================================================================
// Uncomment the Export and evaluation() call below to run evaluation.

var predicted = trainingSamples.classify(regressor);

/*
Export.table.toDrive({
  collection: predicted,
  description: 'future_heat_rf_samples_' + modelName,
  fileFormat: 'CSV',
  fileNamePrefix: 'future_heat_rf_samples_' + modelName,
  folder: '{change to your folder name}',
});
*/

function evaluation() {
  // Variable importance
  var importance = ee.Dictionary(regressor.explain().get('importance'));
  print('Variable importance', importance);

  // Compute error metrics
  var evaluated = predicted.map(function(f) {
    var trueValue = f.getNumber('HWD');
    var predValue = f.getNumber('classification');
    var error = predValue.subtract(trueValue);
    return f.set({
      predicted: predValue,
      error: error,
      absError: error.abs(),
      sqError: error.pow(2)
    });
  });

  var mae = evaluated.aggregate_mean('absError');
  var rmse = evaluated.aggregate_mean('sqError').sqrt();

  // Compute R² manually from covariance
  var statsHWD = evaluated.aggregate_stats('HWD');
  var statsPred = evaluated.aggregate_stats('predicted');
  var meanX = statsHWD.get('mean');
  var meanY = statsPred.get('mean');

  var covXY = evaluated.aggregate_array('HWD')
    .zip(evaluated.aggregate_array('predicted'))
    .map(function(pair) {
      pair = ee.List(pair);
      return ee.Number(pair.get(0)).subtract(meanX)
        .multiply(ee.Number(pair.get(1)).subtract(meanY));
    }).reduce(ee.Reducer.sum());

  var varX = statsHWD.get('sample_sd');
  var varY = statsPred.get('sample_sd');
  var n = evaluated.size();
  
  var r = ee.Number(covXY).divide(n.multiply(varX).multiply(varY));
  var r2 = r.pow(2);
  
  print('MAE', mae);
  print('RMSE', rmse);
  print('R²', r2);
}
// evaluation();


// =============================================================================
// Step 7: Predict Historical Annual Extreme Heat Days (2000–2014)
// =============================================================================

var histImage = ee.Image([]);

for (var i = 2000; i < 2015; i++) {
  var y = ee.Number(i).toInt();
  var year = y.format();

  var annualVars = getMeanVars(y, y, 'historical');
  var prediction = annualVars.classify(regressor)
    .rename(ee.String('HWD_').cat(year))
    .set('year', y);

  histImage = histImage.addBands(prediction);
}

print('Historical prediction image - ' + modelName, histImage);

Export.image.toAsset({
  image: histImage,
  description: 'heat_days_historical_2000_2014_' + modelName,
  assetId: 'projects/{change to your assets name}/heat_days_historical_2000_2014_' + modelName,
  region: AOI,
  scale: targetScale,
  crs: 'EPSG:4326',
  maxPixels: 1e13
});

Map.addLayer(histImage.select('HWD_2000'), {min: 0, max: 50, palette: ['blue', 'yellow', 'red']}, 'Predicted HWD 2000', false);
Map.addLayer(histImage.select('HWD_2014'), {min: 0, max: 50, palette: ['blue', 'yellow', 'red']}, 'Predicted HWD 2014', false);


// =============================================================================
// Step 8: Predict Future Annual Extreme Heat Days (2020–2100, decadal)
// =============================================================================
// SSP126 is not available in NASA/GDDP-CMIP6; a pre-exported image asset is
// used instead. SSP245 and SSP585 are queried directly from the collection.

// Helper function: retrieve band names for a given year from the SSP126 band index asset
function getBandsByYear(bandIndex, year, variables) {
  var yearStr = ee.Number(year).format();
  var bandNames = variables.map(function(v) {
    return ee.String(v).cat('_').cat(yearStr);
  });

  return bandIndex
    .filter(ee.Filter.inList('name', bandNames))
    .sort('band')
    .aggregate_array('band')
    .map(function(i) {
      return ee.String('b').cat(ee.Number(i).format());
    });
}

// Load pre-exported SSP126 CMIP6 image and its band index
var band_index = ee.FeatureCollection("projects/ee-thutyecology/assets/Hazard/ssp126_2020_2100_band_index");
var cmip6_image = ee.Image("projects/ee-thutyecology/assets/Hazard/ssp126_2020_2100_" + modelName)
  .resample('bilinear')
  .reproject({crs: 'EPSG:4326', scale: targetScale});

// Loop over all three SSP scenarios
for (var j = 0; j < 3; j++) {
  var scenario = scenarios[j];

  var futureYears = ee.List.sequence(futureStart, futureEnd);
  var futureImage = ee.Image([]);

  // Predict at decadal intervals (2020, 2030, ..., 2100)
  for (var i = 0; i < futureYears.length().getInfo(); i += 10) {
    var y = ee.Number(futureYears.get(i)).toInt();
    var year = y.format();

    if (scenario == 'ssp126') {
      // SSP126 is not available in NASA/GDDP-CMIP6; use pre-exported image asset instead
      var bandNames = getBandsByYear(band_index, y, varList);
      var annualVars = cmip6_image.select(bandNames).rename(varList);
    } else {
      var annualVars = getMeanVars(y, y, scenario);
    }

    var prediction = annualVars.classify(regressor)
      .rename(ee.String('HWD_').cat(year))
      .set('year', y);

    futureImage = futureImage.addBands(prediction);
  }

  print('Future prediction image - ' + scenario, futureImage);
  
  Export.image.toAsset({
    image: futureImage,
    description: 'heat_days_predicted_' + futureStart + '_' + futureEnd + '_' + modelName + '_' + scenario,
    assetId: 'projects/{change to your assets name}/heat_days_predicted_' + futureStart + '_' + futureEnd + '_' + modelName + '_' + scenario,
    region: AOI,
    scale: targetScale,
    crs: 'EPSG:4326',
    maxPixels: 1e13
  });
}

Map.addLayer(futureImage.select('HWD_2020'), {min: 0, max: 50, palette: ['blue', 'yellow', 'red']}, 'Predicted HWD 2020 ' + scenario, false);
Map.addLayer(futureImage.select('HWD_2050'), {min: 0, max: 50, palette: ['blue', 'yellow', 'red']}, 'Predicted HWD 2050 ' + scenario);
Map.addLayer(futureImage.select('HWD_2070'), {min: 0, max: 50, palette: ['blue', 'yellow', 'red']}, 'Predicted HWD 2070 ' + scenario, false);