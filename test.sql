-- Need enough data to show another library. We'll use Harry Potter and the Sorcerer's Stone (ISBN: 9781781100486)
-- We'll have one copy in the same zip code and one in a nearby zip code
DO $$
DECLARE
  user_id INT;
  user_id_2 INT;
  author_id INT;
  work_id INT;
  edition_id INT;
BEGIN
  INSERT INTO users (email, password, first_name, last_name, zip_code, library_name) VALUES ('john@youlib.com', '1234', 'John', 'Smith', '60656', 'John S''s Library') RETURNING id INTO user_id;
  INSERT INTO users (email, password, first_name, last_name, zip_code, library_name) VALUES ('mike@youlib.com', '1234', 'Mike', 'Trapp', '60631', 'Mike T''s Library') RETURNING id INTO user_id_2;

  INSERT INTO authors (name) VALUES ('J.K. Rowling') RETURNING id INTO author_id;
  INSERT INTO works (title, description) VALUES ('Harry Potter and the Sorcerer''s Stone', 'Turning the envelope over, his hand trembling, Harry saw a purple wax seal bearing a coat of arms; a lion, an eagle, a badger and a snake surrounding a large letter ''H''. Harry Potter has never even heard of Hogwarts when the letters start dropping on the doormat at number four, Privet Drive. Addressed in green ink on yellowish parchment with a purple seal, they are swiftly confiscated by his grisly aunt and uncle. Then, on Harry''s eleventh birthday, a great beetle-eyed giant of a man called Rubeus Hagrid bursts in with some astonishing news: Harry Potter is a wizard, and he has a place at Hogwarts School of Witchcraft and Wizardry. An incredible adventure is about to begin! Having become classics of our time, the Harry Potter eBooks never fail to bring comfort and escapism. With their message of hope, belonging and the enduring power of truth and love, the story of the Boy Who Lived continues to delight generations of new readers.') RETURNING id INTO work_id;
  INSERT INTO work_authors (work_id, author_id) VALUES (work_id, author_id);
  INSERT INTO editions (work_id, isbn, publisher, published_date, thumbnail) VALUES (work_id, '9781781100486', 'Pottermore Publishing', '2015-12-08', 'http://books.google.com/books/content?id=wrOQLV6xB-wC&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api') RETURNING id INTO edition_id;

  -- Now add edition to both users
  INSERT INTO user_editions (edition_id, user_id) VALUES (edition_id, user_id);
  INSERT INTO user_editions (edition_id, user_id) VALUES (edition_id, user_id_2);
END;
$$;

