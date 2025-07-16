-- Create the database,
CREATE DATABASE  clinic_db;

-- Switch to the newly created database.
USE clinic_db;

--
-- Table structure for table `users`
-- Stores login credentials and roles for all system users.
--
CREATE TABLE IF NOT EXISTS `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(100) NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` enum('doctor','nurse','patient') NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Table structure for table `patients`
-- Stores detailed information for patients. Linked to a user account.
--
CREATE TABLE IF NOT EXISTS `patients` (
  `id` int NOT NULL AUTO_INCREMENT,
  `first_name` varchar(100) NOT NULL,
  `last_name` varchar(100) NOT NULL,
  `age` int DEFAULT NULL,
  `gender` varchar(10) DEFAULT NULL,
  `user_id` int DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `patients_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Table structure for table `prescriptions`
-- Stores all medication prescriptions. Linked to a patient and a doctor.
--
CREATE TABLE IF NOT EXISTS `prescriptions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `patient_id` int DEFAULT NULL,
  `doctor_id` int DEFAULT NULL,
  `drug_name` varchar(255) NOT NULL,
  `date` datetime NOT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`id`),
  KEY `fk_prescription_patient` (`patient_id`),
  KEY `fk_prescription_doctor` (`doctor_id`),
  CONSTRAINT `fk_prescription_doctor` FOREIGN KEY (`doctor_id`) REFERENCES `users` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_prescription_patient` FOREIGN KEY (`patient_id`) REFERENCES `patients` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Table structure for table `test_results`
-- Stores all lab/test results. Linked to a patient and a nurse.
--
CREATE TABLE IF NOT EXISTS `test_results` (
  `id` int NOT NULL AUTO_INCREMENT,
  `patient_id` int DEFAULT NULL,
  `nurse_id` int DEFAULT NULL,
  `test_name` varchar(255) NOT NULL,
  `result` text,
  `date` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_test_result_patient` (`patient_id`),
  KEY `fk_test_result_nurse` (`nurse_id`),
  CONSTRAINT `fk_test_result_nurse` FOREIGN KEY (`nurse_id`) REFERENCES `users` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_test_result_patient` FOREIGN KEY (`patient_id`) REFERENCES `patients` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --- End of Script ---
