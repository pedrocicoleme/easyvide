$(document).ready(function(){
    $(".button-collapse").sideNav();
    $('.modal-trigger').leanModal();

    //$("#live_stream_img").attr("src",$("#live_stream_img").data("src"));
});

var app = angular.module('easyvideApp', ['ui.materialize', 'ngRoute']);

// this way there is no conflict between jinja and angularjs
app.config(['$interpolateProvider', function($interpolateProvider) {
    $interpolateProvider.startSymbol('[[');
    $interpolateProvider.endSymbol(']]');
}]);


app.config(['$routeProvider', function($routeProvider) {
  $routeProvider.
    when("/cameras", {templateUrl: "static/partials/cameras.html", controller: "CamerasCtrl"}).
    when("/drivers/:id", {templateUrl: "partials/driver.html", controller: "driverController"}).
    otherwise({redirectTo: '/drivers'});
}]);

app.controller('CamerasCtrl', function ($scope, $http, $routeParams) {
    var init = function () {
        $scope.loadCameras();

        if ($routeParams.add_new) {
            $scope.addCamera();
        }
    };
    init();

    $scope.loadCameras = function () {
        $http.get('/api/camera/list').
        success(function(data, status, headers, config) {
            $scope.cameras = data['cameras'];
        }).
        error(function(data, status, headers, config) {
            // log error
            alert('error getting cameras');
        });
    };

    $scope.addCamera = function () {
        //$scope.cameras.push({});
    };

    // $scope.addCamera();
});