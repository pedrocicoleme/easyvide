$(document).ready(function(){
    $(".button-collapse").sideNav();

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
        controller: 'CameraNewCtrl'
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

app.controller('CamerasCtrl', function($scope, $http, $routeParams) {
    $scope.loadCameras = function () {
        console.log('retrieving cameras from server');
        $http.get('/api/camera/list').
        success(function(data, status, headers, config) {
            $scope.cameras = data['cameras'];
        }).
        error(function(data, status, headers, config) {
            // log error
            alert('error getting cameras');
        });
    };

    $scope.$on('cameras', function (event, data) {
        console.log(data); // 'Some data'

        if (data == 'refresh') {
            $scope.loadCameras();
        }
    });

    var init = function () {
        $scope.loadCameras();
    };
    init();
});

app.controller('CameraNewCtrl', function($scope, $http, $routeParams, $state) {
    var init = function () {
        $('#modal1').openModal({
            complete: function() { alert('Closed'); $state.go('^'); $scope.$emit('cameras', 'refresh'); }
        });
    };
    init();
});