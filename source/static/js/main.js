$(document).ready(function(){
    $(".button-collapse").sideNav();
    $('.modal-trigger').leanModal();

    //$("#live_stream_img").attr("src",$("#live_stream_img").data("src"));
});

var app = angular.module('easyvideApp', ['ui.materialize', 'ngRoute', 'ui.router']);

// this way there is no conflict between jinja and angularjs
app.config(['$interpolateProvider', function($interpolateProvider) {
    $interpolateProvider.startSymbol('[[');
    $interpolateProvider.endSymbol(']]');
}]);

app.config(function($stateProvider, $routeProvider) {
    //
    // For any unmatched url, redirect to /state1
    $routeProvider.otherwise("/cameras");
    //
    // Now set up the states
    $stateProvider
    .state('cameras', {
        url: '/cameras',
        templateUrl: 'static/partials/cameras.html',
        controller: 'CamerasCtrl'
    })
    .state('cameras.add_new', {
        url: '/add_new',
        templateUrl: 'static/partials/cameras.add_new.html',
        controller: function($scope) {
            console.log('where is the new camera?');
            alert('new camera modal should appear');
        }
    })
    .state('state2', {
        url: "/state2",
        templateUrl: "partials/state2.html"
    })
    .state('state2.list', {
        url: "/list",
        templateUrl: "partials/state2.list.html",
        controller: function($scope) {
        $scope.things = ["A", "Set", "Of", "Things"];
        }
    });
});

app.controller('CamerasCtrl', function ($scope, $http, $routeParams) {
    alert('hello, I\'m CamerasCtrl')
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

    var init = function () {
        $scope.loadCameras();

        if ($routeParams.add_new) {
            $scope.addCamera();
        }

        alert('hei');
    };
    init();
});