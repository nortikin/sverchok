float max_distance;
PImage img1;
PImage img2;
PImage img3;
PImage img4;

      void setup() {
        size(800,150);
        img1 = loadImage("../town640.jpg");
        img2 = loadImage("../lgsm.jpg");
        img3 = loadImage("../umbsm.jpg");
        img4 = loadImage("../trusssm.jpg");
      }
      
      void draw() {
        background(255,255,255,255); //background(152,179,171);
        
        fill( 150,100,50 );
        stroke( 255 );// c, 100,  100+random(150));
        strokeWeight(3);
        image(img1, 0, 0, 200, 150);
        image(img2, 200, 0, 200, 150);
        image(img3, 400, 0, 200, 150);
        image(img4, 600, 0, 200, 150);
      }
      
