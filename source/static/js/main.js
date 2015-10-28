// $(document).ready(function(){
//     $(".button-collapse").sideNav();

//     $("#live_stream_img").attr("src",$("#live_stream_img").data("src"));
// });

var app = angular.module('easyvideApp', ['ui.materialize', 'ngRoute']);
 
app.config(['$interpolateProvider', function($interpolateProvider) {
    $interpolateProvider.startSymbol('[[');
    $interpolateProvider.endSymbol(']]');
}]);

app.controller('CameraListCtrl', function ($scope, $http) {
    $http.get('/api/camera/list').
    success(function(data, status, headers, config) {
        $scope.cameras = data['cameras'];
    }).
    error(function(data, status, headers, config) {
        // log error
        alert('error getting cameras');
    });

    $scope.addCamera = function () {
        $scope.cameras.push({});
    };

    // $scope.addCamera();
});