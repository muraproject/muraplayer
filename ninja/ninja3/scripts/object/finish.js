var layer = require("scripts/layer");
var tween = require("scripts/lib/tween");
var timeline = require("scripts/timeline");
var message = require("scripts/message");
var state = require("scripts/state");

var exponential = tween.exponential.co;

exports.anims = [];

exports.set = function(){
    this.image = layer.createImage("default", "images/finish.png", 75, 198, 490, 85).hide().scale(1e-5, 1e-5);
    this.nextButton = layer.createImage("default", "images/next-button.png", 270, 300, 100, 50).hide().scale(1e-5, 1e-5);
};

exports.show = function(start){
    timeline.createTask({
        start: start, duration: 500, data: [1e-5, 1, "show"],
        object: this, onTimeUpdate: this.onZooming, onTimeStart: this.onZoomStart, onTimeEnd: this.onZoomEnd,
        recycle: this.anims
    });
};

exports.hide = function(start){
    timeline.createTask({
        start: start, duration: 500, data: [1, 1e-5, "hide"],
        object: this, onTimeUpdate: this.onZooming, onTimeStart: this.onZoomStart, onTimeEnd: this.onZoomEnd,
        recycle: this.anims
    });
};

exports.onZoomStart = function(sz, ez, mode){
    if(mode == "show"){
        this.image.show();
        this.nextButton.show();
    }
};

exports.onZooming = function(time, sz, ez, z){
    this.image.scale(z = exponential(time, sz, ez - sz, 500), z);
    this.nextButton.scale(z, z);
};

exports.onZoomEnd = function(sz, ez, mode){
    if(mode == "show"){
        state("click-enable").on();
        message.addEventListener("click", this.onClick);
    } else if(mode === "hide"){
        this.image.hide();
        this.nextButton.hide();
        message.removeEventListener("click", this.onClick);
    }
};

exports.onClick = function(e){
    var locX = e.clientX - canvas.offsetLeft;
    var locY = e.clientY - canvas.offsetTop;
    
    if(locX >= 270 && locX <= 370 && locY >= 300 && locY <= 350){
        console.log("Next button clicked!");
        // Add your next level logic here
    }
};