// A flag to know when start or stop the camera
var enabled = false;
// Use require to add webcamjs
var WebCamera = require('webcamjs');

// https://ourcodeworld.com/articles/read/134/how-to-use-the-camera-with-electron-framework-create-a-snapshot-and-save-the-image-on-the-system
window.addEventListener(
    'load',
    function() {
        if (!enabled) {
            // Start the camera !
            enabled = true;
            WebCamera.attach('#camdemo');
            console.log('The camera has been started');
        } else {
            // Disable the camera !
            enabled = false;
            WebCamera.reset();
            console.log('The camera has been disabled');
        }
    },
    false
);