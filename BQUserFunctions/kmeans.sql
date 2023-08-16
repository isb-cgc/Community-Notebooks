CREATE OR REPLACE FUNCTION `__PROJECTID__.__DATASET__.kmeans__VERSIONTAG__`(PointSet ARRAY<STRUCT<point ARRAY<FLOAT64>>>, iterations INT64, k INT64)
RETURNS ARRAY<INT64> 
LANGUAGE js 
OPTIONS(description="Estimates cluster assigments using the K-means algorithm (https://en.wikipedia.org/wiki/K-means_clustering), implemented in JavaScript.\nPARAMETERS: PointSet ( ARRAY<STRUCT<point ARRAY<FLOAT64>>>, the data in the form of an array of structures where each element(point) is an array that represents a data point. All the data points should have the same dimension), iterations (INT64, the number of iterations), and k (the number of clusters, INT64).\nOUTPUT: An array of labels (integer numbers) representing the cluster assigments for each data point.\nVERSION: 1.0\nNOTE: The code was adapted from https://github.com/NathanEpstein/clusters \nEXAMPLE:https://github.com/isb-cgc/Community-Notebooks/tree/master/BQUserFunctions")
AS """
'use strict'

function sumOfSquareDiffs(oneVector, anotherVector) {
  // the sum of squares error //
  var squareDiffs = oneVector.map(function(component, i) {
    return Math.pow(component - anotherVector[i], 2);
  });
  return squareDiffs.reduce(function(a, b) { return a + b }, 0);
};

function mindex(array) {
  // returns the index to the minimum value in the array
  var min = array.reduce(function(a, b) {
    return Math.min(a, b);
  });
  return array.indexOf(min);
};

function sumVectors(a, b) {
  // The map function gets used frequently in JavaScript
  return a.map(function(val, i) { return val + b[i] });
};

function averageLocation(points) {
  // Take all the points assigned to a cluster
  // and find the averge center point.
  // This gets used to update the cluster centroids.
  var zeroVector = points[0].location.map(function() { return 0 });
  var locations = points.map(function(point) { return point.location });
  var vectorSum = locations.reduce(function(a, b) { return sumVectors(a, b) }, zeroVector);
  return vectorSum.map(function(val) { return val / points.length });
};

function Point(location) {
  // A point object, each sample is represented as a point //
  var self = this;
  this.location = location;
  this.label = 1;
  this.updateLabel = function(centroids) {
    var distancesSquared = centroids.map(function(centroid) {
      return sumOfSquareDiffs(self.location, centroid.location);
    });
    self.label = mindex(distancesSquared);
  };
};


function Centroid(initialLocation, label) {
  // The cluster centroids //
  var self = this;
  this.location = initialLocation;
  this.label = label;
  this.updateLocation = function(points) {
    var pointsWithThisCentroid = points.filter(function(point) { return point.label == self.label });
    if (pointsWithThisCentroid.length > 0) {
      self.location = averageLocation(pointsWithThisCentroid);
    }
  };
};


var data = [];

// Our data list is list of lists. The small list being each (x,y) point
for (var i = 0; i < PointSet.length; i++) {
  data.push( PointSet[i].point )
}
// initialize point objects with data
var points = data.map(function(vector) { return new Point(vector) });


// intialize centroids
var centroids = [];
for (var i = 0; i < k; i++) {
  centroids.push(new Centroid(points[i % points.length].location, i));
};


// update labels and centroid locations until convergence
for (var iter = 0; iter < iterations; iter++) {
  points.forEach(function(point) { point.updateLabel(centroids) });
  centroids.forEach(function(centroid) { centroid.updateLocation(points) });
};

// return the cluster labels.
var labels = []
for (var i = 0; i < points.length; i++) {
  labels.push(points[i].label)
}
return labels;
""";
