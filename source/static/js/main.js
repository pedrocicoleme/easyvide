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
    // For any unmatched url, redirect to /state1
    $routeProvider.otherwise("/cameras");
    
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
});

app.controller('AppCtrl', function($scope, $http, $routeParams) {
    $scope.setEnableMotion = function() {
        enable = '0';
        if ($scope.enableMotion == true) {
            enable = '1';
        }

        $http.get('/api/state/' + enable).
        success(function(data, status, headers, config) {
            $scope.enableMotion = data['enable_motion'];
        }).
        error(function(data, status, headers, config) {
            // log error
            alert('error getting state');
        });
    }

    var init = function() {
        $http.get('/api/state').
        success(function(data, status, headers, config) {
            $scope.enableMotion = data['enable_motion'];
        }).
        error(function(data, status, headers, config) {
            // log error
            alert('error getting state');
        });
    }
    init();
});

app.controller('CamerasCtrl', function($scope, $http, $routeParams) {
    $scope.loadCameras = function() {
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

    $scope.updateCamera = function($index) {
        console.log($scope.cameras[$index]);
        $http({
            url: '/api/camera/' + $scope.cameras[$index]['cameraID'],
            method: 'PUT',
            data: JSON.stringify($scope.cameras[$index]),
            headers: {'Content-Type': 'application/json'}
        }).
        success(function(data, status, headers, config) {
            alert(data.message);
            
            $scope.loadCameras();
        }).
        error(function(data, status, headers, config) {
            alert('error during request');
        });
    }

    $scope.deleteCamera = function($index) {
        console.log($scope.cameras[$index]);
        $http({
            url: '/api/camera/' + $scope.cameras[$index]['cameraID'],
            method: 'DELETE',
            data: JSON.stringify($scope.cameras[$index]),
            headers: {'Content-Type': 'application/json'}
        }).
        success(function(data, status, headers, config) {
            alert(data.message);
            
            $scope.loadCameras();
        }).
        error(function(data, status, headers, config) {
            alert('error during request');
        });
    }

    $scope.$on('cameras', function(event, data) {
        console.log(data); // 'Some data'

        if (data == 'refresh') {
            $scope.loadCameras();
        }
    });

    var init = function() {
        $scope.loadCameras();
    };
    init();
});

app.controller('CameraNewCtrl', function($scope, $http, $routeParams, $state) {
    var init = function () {
        $('#modal1').openModal({
            complete: function() { del(); }
        });
    };
    init();

    $scope.addCamera = function() {
        console.log($scope.camera);

        $http({
            url: '/api/camera',
            method: 'POST',
            data: JSON.stringify($scope.camera),
            headers: {'Content-Type': 'application/json'}
        }).
        success(function(data, status, headers, config) {
            alert(data.message);
            del();
        }).
        error(function(data, status, headers, config) {
            alert('error during request');
        });
    };

    var del = function() {
        $('#modal1').closeModal();

        console.log('new camera modal closed');

        $state.go('^');

        $scope.$emit('cameras', 'refresh');
    }
});