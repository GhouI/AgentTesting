const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
const gridSize = 20;
const canvasSize = 400;
let snake = [ { x: 160, y: 160 }, { x: 140, y: 160 }, { x: 120, y: 160 }, { x: 100, y: 160 }];
let dx = gridSize;
let dy = 0;
let food = { x: 0, y: 0 };
let changingDirection = false;
let score = 0;

function getRandomFoodPosition() {
    return {
        x: Math.floor(Math.random() * (canvasSize/gridSize)) * gridSize,
        y: Math.floor(Math.random() * (canvasSize/gridSize)) * gridSize
    };
}

function drawSnakePart(snakePart) {
    ctx.fillStyle = '#00FF00';
    ctx.strokeStyle = '#000000';
    ctx.fillRect(snakePart.x, snakePart.y, gridSize, gridSize);
    ctx.strokeRect(snakePart.x, snakePart.y, gridSize, gridSize);
}

function drawSnake() {
    snake.forEach(drawSnakePart);
}

function drawFood() {
    ctx.fillStyle = '#FF0000';
    ctx.strokeStyle = '#000000';
    ctx.fillRect(food.x, food.y, gridSize, gridSize);
    ctx.strokeRect(food.x, food.y, gridSize, gridSize);
}

function advanceSnake() {
    const head = { x: snake[0].x + dx, y: snake[0].y + dy };
    snake.unshift(head);

    if (head.x === food.x && head.y === food.y) {
        score += 10;
        food = getRandomFoodPosition();
    } else {
        snake.pop();
    }
}

function changeDirection(event) {
    const LEFT_KEY = 37;
    const RIGHT_KEY = 39;
    const UP_KEY = 38;
    const DOWN_KEY = 40;

    if (changingDirection) return;
    changingDirection = true;

    const keyPressed = event.keyCode;
    const goingUp = dy === -gridSize;
    const goingDown = dy === gridSize;
    const goingRight = dx === gridSize;
    const goingLeft = dx === -gridSize;

    if (keyPressed === LEFT_KEY && !goingRight) {
        dx = -gridSize;
        dy = 0;
    }

    if (keyPressed === UP_KEY && !goingDown) {
        dx = 0;
        dy = -gridSize;
    }

    if (keyPressed === RIGHT_KEY && !goingLeft) {
        dx = gridSize;
        dy = 0;
    }

    if (keyPressed === DOWN_KEY && !goingUp) {
        dx = 0;
        dy = gridSize;
    }
}

function checkCollision() {
    for (let i = 4; i < snake.length; i++) {
        if (snake[i].x === snake[0].x && snake[i].y === snake[0].y)
            return true;
    }

    return snake[0].x < 0 || snake[0].x >= canvasSize ||
           snake[0].y < 0 || snake[0].y >= canvasSize;
}

function gameLoop() {
    if (checkCollision()) return;

    changingDirection = false;
    setTimeout(function onTick() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        drawFood();
        advanceSnake();
        drawSnake();
        gameLoop();
    }, 100);
}

document.addEventListener('keydown', changeDirection);
food = getRandomFoodPosition();
gameLoop();