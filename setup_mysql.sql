CREATE DATABASE 'discord';
CREATE USER 'discord'@'%' IDENTIFIED BY 'discord';
GRANT INSERT, UPDATE, DELETE, EXECUTE ON discord.* TO 'discord';

USE discord;

CREATE TABLE settings (
    name VARCHAR(64) NOT NULL PRIMARY KEY,
    value VARCHAR(128) NOT NULL
);


CREATE TABLE guild_channels (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    channel_type VARCHAR(64) NOT NULL,
    channel_id BIGINT NOT NULL
);


CREATE TABLE rss_feeds (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    unique_name VARCHAR(64) UNIQUE NOT NULL,
    url VARCHAR(256) NOT NULL
);


CREATE TABLE rss_feed_subscribers (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    rss_feed_id INTEGER REFERENCES rss_feeds(id),
    channel_id BIGINT NOT NULL
);


CREATE TABLE radio_stations (
    unique_name VARCHAR(64) NOT NULL PRIMARY KEY,
    display_name VARCHAR(256) NOT NULL,
    url VARCHAR(256) NOT NULL,
    is_opus BOOLEAN NOT NULL
);


DELIMITER $$
CREATE PROCEDURE insert_or_update_guild_channel
(
	input_guild_id BIGINT, 
    input_channel_type VARCHAR(64), 
    input_channel_id BIGINT
)
BEGIN
    IF EXISTS (SELECT channel_id FROM guild_channels WHERE guild_id=input_guild_id AND channel_type=input_channel_type) THEN
        UPDATE guild_channels SET channel_id=input_channel_id WHERE guild_id=input_guild_id AND channel_type=input_channel_type;
    ELSE
        INSERT INTO guild_channels (guild_id, channel_type, channel_id) VALUES (input_guild_id, input_channel_type, input_channel_id);
    END IF;
    SELECT ROW_COUNT();
END $$
DELIMITER ;


DELIMITER $$
CREATE PROCEDURE insert_or_update_radio_station
(
	input_unique_name VARCHAR(64), 
    input_display_name VARCHAR(128), 
    input_url VARCHAR(256),
    input_is_opus BOOLEAN
)
BEGIN
    IF EXISTS (SELECT unique_name FROM radio_stations WHERE unique_name=input_unique_name) THEN
        UPDATE radio_stations SET display_name=input_display_name, url=input_url, is_opus=input_is_opus WHERE unique_name=input_unique_name;
    ELSE
        INSERT INTO radio_stations (unique_name, display_name, url, is_opus) VALUES (input_unique_name, input_display_name, input_url, input_is_opus);
    END IF;
    SELECT ROW_COUNT();
END $$
DELIMITER ;


DELIMITER $$
CREATE PROCEDURE insert_or_update_rss_feed
(
	input_unique_name VARCHAR(64), 
    input_url VARCHAR(256)
)
BEGIN
    IF EXISTS (SELECT unique_name FROM rss_feeds WHERE unique_name=input_unique_name) THEN
        UPDATE rss_feeds SET url=input_url WHERE unique_name=input_unique_name;
    ELSE
        INSERT INTO rss_feeds (unique_name, url) VALUES (input_unique_name, input_url);
    END IF;
    SELECT ROW_COUNT();
END $$
DELIMITER ;


DELIMITER $$
CREATE PROCEDURE subscribe_to_rss_feed
(
	feed_name VARCHAR(64), 
    input_channel_id BIGINT
)
BEGIN
    SET @feed_id = (SELECT id FROM rss_feeds WHERE unique_name=feed_name);
    IF @feed_id IS NOT NULL AND NOT EXISTS (SELECT * FROM rss_feeds AS f RIGHT JOIN rss_feed_subscribers AS s ON f.id=s.rss_feed_id WHERE f.unique_name=feed_name AND s.channel_id=input_channel_id) THEN
        INSERT INTO rss_feed_subscribers (rss_feed_id, channel_id) VALUES (@feed_id, input_channel_id);
    END IF;
    SELECT ROW_COUNT();
END $$
DELIMITER ;


DELIMITER $$
CREATE PROCEDURE unsubscribe_to_rss_feed
(
	feed_name VARCHAR(64), 
    input_channel_id BIGINT
)
BEGIN
    SET @feed_id = (SELECT id FROM rss_feeds WHERE unique_name=feed_name);
    IF @feed_id IS NOT NULL AND EXISTS (SELECT * FROM rss_feeds AS f RIGHT JOIN rss_feed_subscribers AS s ON f.id=s.rss_feed_id WHERE f.unique_name=feed_name AND s.channel_id=input_channel_id) THEN
        DELETE FROM rss_feed_subscribers WHERE rss_feed_id=@feed_id AND channel_id=input_channel_id;
    END IF;
    SELECT ROW_COUNT();
END $$
DELIMITER ;


DELIMITER $$
CREATE PROCEDURE insert_or_update_settings
(
	input_name VARCHAR(64), 
    input_value VARCHAR(128)
)
BEGIN
    IF EXISTS (SELECT name FROM settings WHERE name=input_name) THEN
        UPDATE settings SET value=input_value WHERE name=input_name;
    ELSE
        INSERT INTO settings (name, value) VALUES (input_name, input_value);
    END IF;
    SELECT ROW_COUNT();
END $$
DELIMITER ;

-- ----------------------------
-- Quotes
-- ----------------------------

CREATE TABLE quotes (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    set_id BIGINT NOT NULL,
    ordering INT NOT NULL,
    guild_id BIGINT,
    author NVARCHAR(5000),
    time_place NVARCHAR(5000),
    quote NVARCHAR(5000),
    date_created DATETIME
) CHARSET=utf16;


DELIMITER $$
CREATE PROCEDURE insert_quote_with_set_id
(
    input_set_id BIGINT,
    input_ordering INT,
    input_guild_id BIGINT,
	input_quote NVARCHAR(5000), 
    input_author NVARCHAR(5000),
    input_time_place NVARCHAR(5000)
)
BEGIN
    INSERT INTO quotes (set_id, ordering, guild_id, author, time_place, quote, date_created) VALUES (input_set_id, input_ordering, input_guild_id, input_author, input_time_place, input_quote, NOW());
    SELECT ROW_COUNT();
END $$
DELIMITER ;


CREATE TABLE qotd_subscription (
    guild_id BIGINT UNIQUE NOT NULL,
    channel_id BIGINT NOT NULL
);


DELIMITER $$
CREATE PROCEDURE subscribe_to_qotd
(
	input_guild_id BIGINT, 
    input_channel_id BIGINT
)
BEGIN
    IF EXISTS (SELECT * FROM qotd_subscription WHERE guild_id=input_guild_id) THEN
        UPDATE qotd_subscription SET channel_id=input_channel_id WHERE guild_id=input_channel_id;
    ELSE
        INSERT INTO qotd_subscription (guild_id, channel_id) VALUES (input_guild_id, input_channel_id);
    END IF;
    SELECT ROW_COUNT();
END $$
DELIMITER ;

