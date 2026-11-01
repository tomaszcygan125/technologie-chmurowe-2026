CREATE TABLE products (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  description VARCHAR(255)
) ENGINE=InnoDB;

CREATE TABLE materials (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  quantity INT NOT NULL DEFAULT 0,
  minimum_quantity INT NOT NULL DEFAULT 0
) ENGINE=InnoDB;

CREATE TABLE product_materials (
  product_id INT NOT NULL,
  material_id INT NOT NULL,
  quantity_required INT NOT NULL,
  PRIMARY KEY (product_id, material_id),
  FOREIGN KEY (product_id) REFERENCES products(id),
  FOREIGN KEY (material_id) REFERENCES materials(id)
) ENGINE=InnoDB;

CREATE TABLE orders (
  id INT AUTO_INCREMENT PRIMARY KEY,
  product_id INT NOT NULL,
  quantity INT NOT NULL,
  status VARCHAR(20) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (product_id) REFERENCES products(id)
) ENGINE=InnoDB;

CREATE TABLE stock_history (
  id INT AUTO_INCREMENT PRIMARY KEY,
  material_id INT NOT NULL,
  order_id INT NOT NULL,
  quantity_change INT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (material_id) REFERENCES materials(id),
  FOREIGN KEY (order_id) REFERENCES orders(id)
) ENGINE=InnoDB;

INSERT INTO products (name, description) VALUES
 ('Biurko','Blat, 4 nogi, 16 śrub, 2 wsporniki'),
 ('Krzesło','Siedzisko, oparcie, 4 nogi, 8 śrub'),
 ('Półka','2 boki, 3 półki, 12 śrub');

INSERT INTO materials (name, quantity, minimum_quantity) VALUES
 ('Blat',1000000,10),('Noga metalowa',1000000,10),('Śruba',1000000,100),
 ('Wspornik',1000000,10),('Siedzisko',1000000,10),('Oparcie',1000000,10),
 ('Bok półki',1000000,10),('Półka drewniana',1000000,10);

INSERT INTO product_materials VALUES
 (1,1,1),(1,2,4),(1,3,16),(1,4,2),
 (2,5,1),(2,6,1),(2,2,4),(2,3,8),
 (3,7,2),(3,8,3),(3,3,12);