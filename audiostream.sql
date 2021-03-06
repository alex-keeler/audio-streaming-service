-- MySQL Script generated by MySQL Workbench
-- Thu Jun  3 23:53:35 2021
-- Model: New Model    Version: 1.0
-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema audiostream
-- -----------------------------------------------------
DROP SCHEMA IF EXISTS `audiostream` ;

-- -----------------------------------------------------
-- Schema audiostream
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `audiostream` DEFAULT CHARACTER SET utf8 ;
USE `audiostream` ;

-- -----------------------------------------------------
-- Table `audiostream`.`artist`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `audiostream`.`artist` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `name_UNIQUE` (`name` ASC))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `audiostream`.`album`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `audiostream`.`album` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(255) NOT NULL,
  `year_released` INT NULL,
  `artist_id` INT NULL,
  `cover_file_uuid` VARCHAR(36) NULL,
  PRIMARY KEY (`id`),
  INDEX `fk_album_artist_idx` (`artist_id` ASC),
  UNIQUE INDEX `uk_album_name_artist` (`name` ASC, `artist_id` ASC),
  CONSTRAINT `fk_album_artist`
    FOREIGN KEY (`artist_id`)
    REFERENCES `audiostream`.`artist` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `audiostream`.`song`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `audiostream`.`song` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(255) NOT NULL,
  `length` INT NOT NULL,
  `track_number` INT NULL,
  `album_id` INT NULL,
  `file_uuid` VARCHAR(36) NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `fk_song_album1_idx` (`album_id` ASC),
  UNIQUE INDEX `file_uuid_UNIQUE` (`file_uuid` ASC),
  CONSTRAINT `fk_song_album1`
    FOREIGN KEY (`album_id`)
    REFERENCES `audiostream`.`album` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `audiostream`.`playlist`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `audiostream`.`playlist` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(255) NOT NULL,
  `description` VARCHAR(500) NULL,
  `date_created` DATETIME NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `uk_playlist_user_name` (`name` ASC))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `audiostream`.`playlist_song`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `audiostream`.`playlist_song` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `date_added` DATETIME NOT NULL,
  `previous_playlist_song_id` INT NULL,
  `next_playlist_song_id` INT NULL,
  `playlist_group` INT NULL,
  `order` INT NULL,
  `playlist_id` INT NOT NULL,
  `song_id` INT NOT NULL,
  PRIMARY KEY (`id`, `playlist_id`),
  INDEX `fk_playlist_song_next_idx` (`next_playlist_song_id` ASC),
  INDEX `fk_playlist_song_previous_idx` (`previous_playlist_song_id` ASC),
  INDEX `fk_playlist_song_playlist_idx` (`playlist_id` ASC),
  INDEX `fk_playlist_song_song_idx` (`song_id` ASC),
  CONSTRAINT `fk_playlist_song_next`
    FOREIGN KEY (`next_playlist_song_id`)
    REFERENCES `audiostream`.`playlist_song` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_playlist_song_playlist1`
    FOREIGN KEY (`previous_playlist_song_id`)
    REFERENCES `audiostream`.`playlist_song` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_playlist_song_playlist`
    FOREIGN KEY (`playlist_id`)
    REFERENCES `audiostream`.`playlist` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_playlist_song_song`
    FOREIGN KEY (`song_id`)
    REFERENCES `audiostream`.`song` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
