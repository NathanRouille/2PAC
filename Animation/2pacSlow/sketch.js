let nodes = [];
let points = [];
let stages = ['Nodes', 'Block 1', 'Vote 1', 'Block 2', 'Vote 2', 'Election'];
let stageWidth;
let totalSteps = 120; // Number of frames to complete one stage, doublé pour une propagation plus lente
let traits = [];
let restartTime = 10000; // 6 seconds
let simulationEnded = false;
let endTime = 0;
let horizontalDelay = 2000; // 800 milliseconds delay for horizontal alignment with P4
let finalNode = null; // To store the final node
let isPlaying = true; // To track if the simulation is playing
let speedFactor = 5; // Default speed factor

const voteColors = {
  100: 'red',    // R1, S1, T1
  250: 'green',  // R2, S2, T2
  400: 'blue',   // R3, S3, T3
  550: 'orange'  // R4, S4, T4
};

class Node {
  constructor(x, y, label, startDelay) {
    this.x = x;
    this.y = y;
    this.label = label;
    this.sent = false;
    this.stage = 0; // Les nœuds sont toujours au stage 0
    this.startDelay = startDelay;
    this.startTime = millis();
  }

  draw() {
    fill(0);
    ellipse(this.x, this.y, 50, 50);
    fill(255);
    textAlign(CENTER, CENTER);
    text(this.label, this.x, this.y);
  }

  sendTraits() {
    if (!this.sent && millis() - this.startTime >= this.startDelay) {
      for (let point of points) {
        if (point.stage === 1 && this.y !== point.y) {
          let trait = new Trait(this.x, this.y, point.x, point.y, 0, 'blue');
          
          // Ajouter un délai si aligné horizontalement avec P4
          if (this.y === 550) {
            setTimeout(() => traits.push(trait), horizontalDelay);
          } else {
            traits.push(trait);
          }
        }
      }
      this.sent = true;
    }
  }
}

class Point {
  constructor(x, y, label, stage) {
    this.x = x;
    this.y = y;
    this.label = label;
    this.received = 0;
    this.stage = stage;
    this.sent = false;
    this.color = 'black'; // Default color for circles
  }

  draw() {
    stroke(this.color);
    fill(255);
    ellipse(this.x, this.y, 50, 50);
    fill(0);
    noStroke();
    textAlign(CENTER, CENTER);
    text(this.label, this.x, this.y);
  }

  sendTraits() {
    let requiredReceived = (this.stage === 3 || this.stage === 5) ? 2 : 1;

    if (this.received >= requiredReceived && !this.sent) {
      for (let point of points) {
        if (this.stage + 1 === point.stage && this.y !== point.y) {
          let trait = new Trait(this.x, this.y, point.x, point.y, 0, 'blue');
          
          // Ajouter un délai si aligné horizontalement avec P4
          if (this.y === 550) {
            setTimeout(() => traits.push(trait), horizontalDelay);
          } else {
            traits.push(trait);
          }
        }
      }
      this.sent = true;
    }
  }

  receiveTrait(trait) {
    if (this.stage === 2 || this.stage === 4) { // Change color for Vote 1 and Vote 2 stages
      this.color = voteColors[this.y] || 'blue';
      trait.color = this.color;
    }
    this.received++;
  }
}

class Trait {
  constructor(startX, startY, endX, endY, stepProgress, color) {
    this.startX = startX;
    this.startY = startY;
    this.endX = endX;
    this.endY = endY;
    this.stepProgress = stepProgress;
    this.color = color;
    this.arrived = false;
  }

  draw() {
    stroke(this.color);
    strokeWeight(1);
    line(this.startX, this.startY, lerp(this.startX, this.endX, this.stepProgress), lerp(this.startY, this.endY, this.stepProgress));
    if (!this.arrived) {
      this.stepProgress += (1 / totalSteps) * (speedFactor / 5);
      if (this.stepProgress >= 1) {
        this.arrived = true;
        for (let point of points) {
          if (dist(this.endX, this.endY, point.x, point.y) < 1) {
            point.receiveTrait(this);
          }
        }
        // Check if simulation has ended
        if (traits.every(trait => trait.arrived)) {
          if (checkElectionStageCompleted()) {
            simulationEnded = true;
            endTime = millis();
          }
        }
      }
    } else {
      stroke(this.color);
      strokeWeight(1);
      line(this.startX, this.startY, this.endX, this.endY);
    }
  }

  checkArrival() {
    return this.arrived;
  }
}

function setup() {
  createCanvas(1000, 600);
  stageWidth = width / stages.length;
  initializeNodesAndPoints();
  // Event listener for play/stop button
  select('#playStopButton').mousePressed(togglePlayStop);
  // Event listener for speed slider
  select('#speedSlider').input(updateSpeed);
}

function draw() {
  if (isPlaying) {
    background(255);
    drawTimeStages();
    drawPoints();

    for (let node of nodes) {
      node.draw();
      node.sendTraits();
    }

    for (let point of points) {
      point.draw();
      point.sendTraits();
    }

    for (let trait of traits) {
      trait.draw();
    }

    if (simulationEnded) {
      if (!finalNode) {
        // Select a random node label (P1, P2, P3, P4)
        const labels = ['P1', 'P2', 'P3', 'P4'];
        const randomLabel = random(labels);
        // Create a new Node at the right of the canvas
        finalNode = new Node(width - 50, height / 2, randomLabel, 0);
        finalNode.color = 'green'; // Set color to green
      }
      // Draw the final node
      fill('green');
      ellipse(finalNode.x, finalNode.y, 50, 50);
      fill(255);
      textAlign(CENTER, CENTER);
      text(finalNode.label, finalNode.x, finalNode.y);

      if (millis() - endTime >= restartTime) {
        initializeNodesAndPoints();
        simulationEnded = false;
        finalNode = null; // Reset the final node
      }
    }
  }
}

function drawTimeStages() {
  stroke('green');
  strokeWeight(2);
  for (let i = 1; i < stages.length; i++) {
    let x = i * stageWidth;
    for (let y = 0; y < height; y += 10) {
      line(x, y, x, y + 5);
    }
  }

  // Draw stage labels
  fill(0);
  noStroke();
  textAlign(CENTER, CENTER);
  for (let i = 0; i < stages.length; i++) {
    let x = i * stageWidth + stageWidth / 2;
    text(stages[i], x, 30);
  }
}

function drawPoints() {
  fill(0);
  noStroke();
  for (let point of points) {
    for (let i = 1; i < stages.length; i++) {
      let x = i * stageWidth + stageWidth / 2;
      ellipse(x, point.y, 10, 10);
    }
  }
}

function initializeNodesAndPoints() {
  nodes = [];
  points = [];
  traits = [];
  simulationEnded = false;

  nodes.push(new Node(stageWidth / 2, 100, 'P1', 0));
  nodes.push(new Node(stageWidth / 2, 250, 'P2', 0));
  nodes.push(new Node(stageWidth / 2, 400, 'P3', 0));
  nodes.push(new Node(stageWidth / 2, 550, 'P4', 2000)); // Adding a delay of 3000 milliseconds for P4

  points.push(new Point(stageWidth * 1.5, 100, 'Q1', 1));
  points.push(new Point(stageWidth * 1.5, 250, 'Q2', 1));
  points.push(new Point(stageWidth * 1.5, 400, 'Q3', 1));
  points.push(new Point(stageWidth * 1.5, 550, 'Q4', 1));

  points.push(new Point(stageWidth * 2.5, 100, 'R1', 2));
  points.push(new Point(stageWidth * 2.5, 250, 'R2', 2));
  points.push(new Point(stageWidth * 2.5, 400, 'R3', 2));
  points.push(new Point(stageWidth * 2.5, 550, 'R4', 2));

  points.push(new Point(stageWidth * 3.5, 100, 'S1', 3));
  points.push(new Point(stageWidth * 3.5, 250, 'S2', 3));
  points.push(new Point(stageWidth * 3.5, 400, 'S3', 3));
  points.push(new Point(stageWidth * 3.5, 550, 'S4', 3));

  points.push(new Point(stageWidth * 4.5, 100, 'T1', 4));
  points.push(new Point(stageWidth * 4.5, 250, 'T2', 4));
  points.push(new Point(stageWidth * 4.5, 400, 'T3', 4));
  points.push(new Point(stageWidth * 4.5, 550, 'T4', 4));

  points.push(new Point(stageWidth * 5.5, 100, 'U1', 5));
  points.push(new Point(stageWidth * 5.5, 250, 'U2', 5));
  points.push(new Point(stageWidth * 5.5, 400, 'U3', 5));
  points.push(new Point(stageWidth * 5.5, 550, 'U4', 5));
}

function checkElectionStageCompleted() {
  return points.every(point => {
    if (point.stage === 5) {
      return point.received > 0;
    }
    return true;
  });
}

function togglePlayStop() {
  isPlaying = !isPlaying;
  select('#playStopButton').html(isPlaying ? 'Stop' : 'Play');
}

function updateSpeed() {
  speedFactor = select('#speedSlider').value();
}
