CREATE DATABASE IF NOT EXISTS lld_practice;
USE lld_practice;

CREATE TABLE problems (
  id INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  description TEXT NOT NULL,
  constraints TEXT,
  difficulty VARCHAR(20)
);

CREATE TABLE attempts (
  id INT AUTO_INCREMENT PRIMARY KEY,
  problem_id INT NOT NULL,
  learner_id VARCHAR(100) NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'InProgress',
  started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  submitted_at DATETIME NULL,
  FOREIGN KEY (problem_id) REFERENCES problems(id)
);

CREATE TABLE submissions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  attempt_id INT NOT NULL,
  format VARCHAR(20) DEFAULT 'text',
  content TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (attempt_id) REFERENCES attempts(id)
);

CREATE TABLE evaluations (
  id INT AUTO_INCREMENT PRIMARY KEY,
  submission_id INT NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'Pending',
  overall_summary TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  completed_at DATETIME NULL,
  FOREIGN KEY (submission_id) REFERENCES submissions(id)
);

CREATE TABLE rubric_scores (
  id INT AUTO_INCREMENT PRIMARY KEY,
  evaluation_id INT NOT NULL,
  criterion VARCHAR(100) NOT NULL,
  score INT NOT NULL,
  evidence TEXT,
  concern TEXT,
  suggestion TEXT,
  confidence FLOAT,
  FOREIGN KEY (evaluation_id) REFERENCES evaluations(id)
);