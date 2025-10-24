CREATE DATABASE enchentes_db;

CREATE USER 'alagamentos_user'@'localhost' IDENTIFIED BY 'senha123';
GRANT ALL PRIVILEGES ON enchentes_db. * TO 'alagamentos_user'@'localhost';
FLUSH PRIVILEGES;

USE enchentes_db;
CREATE TABLE ocorrencias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    user_name VARCHAR(100) NULL,
    descricao VARCHAR(255) NOT NULL,
    foto_url VARCHAR(512),
    data_ocorrencia TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    latitude DECIMAL(10,8) NOT NULL,
    longitude DECIMAL(11,8) NOT NULL,
    cidade VARCHAR(100),
    condicao VARCHAR(100),
    temperatura_c DECIMAL(5,2),
    umidade INT,
    vento_kph DECIMAL(5,2)
);


CREATE TABLE users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(150) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role ENUM('admin','user') NOT NULL DEFAULT 'user',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE riscos (
  id INT AUTO_INCREMENT PRIMARY KEY,
  cidade VARCHAR(100),
  risco ENUM('BAIXO','MEDIO','ALTO'),
  previsao_chuva_mm FLOAT,
  data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);



