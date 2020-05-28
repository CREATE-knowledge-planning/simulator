var viewer = new Cesium.Viewer('cesiumContainer', {
    shouldAnimate : true
});

viewer.dataSources.add(Cesium.CzmlDataSource.load('./demo.czml'));
viewer.camera.flyHome(0);
