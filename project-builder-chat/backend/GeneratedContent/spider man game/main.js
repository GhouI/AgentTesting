window.onload = function() {
    var config = {
        type: Phaser.AUTO,
        width: window.innerWidth,
        height: window.innerHeight,
        scene: {
            preload: preload,
            create: create,
            update: update
        },
        parent: 'game-container',
    };
    var game = new Phaser.Game(config);

    function preload() {
        // Load assets
    }

    function create() {
        // Initialize game
    }

    function update() {
        // Game loop
    }
};