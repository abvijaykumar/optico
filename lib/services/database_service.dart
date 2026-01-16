import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';
import '../models/models.dart';

class DatabaseService {
  static Database? _database;
  static const String _databaseName = 'optico.db';
  static const int _databaseVersion = 1;

  Future<Database> get database async {
    _database ??= await _initDatabase();
    return _database!;
  }

  Future<Database> _initDatabase() async {
    final databasesPath = await getDatabasesPath();
    final path = join(databasesPath, _databaseName);

    return await openDatabase(
      path,
      version: _databaseVersion,
      onCreate: _onCreate,
      onUpgrade: _onUpgrade,
    );
  }

  Future<void> _onCreate(Database db, int version) async {
    await db.execute('''
      CREATE TABLE songs (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        artist TEXT NOT NULL,
        album TEXT NOT NULL,
        albumArtist TEXT,
        filePath TEXT NOT NULL UNIQUE,
        duration INTEGER NOT NULL,
        trackNumber INTEGER,
        genre TEXT,
        year INTEGER,
        bitrate INTEGER,
        sampleRate INTEGER,
        format TEXT,
        albumArtPath TEXT,
        dateAdded INTEGER,
        lastPlayed INTEGER,
        playCount INTEGER DEFAULT 0,
        isFavorite INTEGER DEFAULT 0
      )
    ''');

    await db.execute('''
      CREATE TABLE playlists (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        coverImagePath TEXT,
        createdAt INTEGER NOT NULL,
        updatedAt INTEGER NOT NULL,
        isSystemPlaylist INTEGER DEFAULT 0
      )
    ''');

    await db.execute('''
      CREATE TABLE playlist_songs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        playlistId TEXT NOT NULL,
        songId TEXT NOT NULL,
        position INTEGER NOT NULL,
        FOREIGN KEY (playlistId) REFERENCES playlists (id) ON DELETE CASCADE,
        FOREIGN KEY (songId) REFERENCES songs (id) ON DELETE CASCADE,
        UNIQUE (playlistId, songId)
      )
    ''');

    await db.execute('''
      CREATE TABLE music_folders (
        id TEXT PRIMARY KEY,
        path TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        songCount INTEGER DEFAULT 0,
        lastScanned INTEGER,
        isEnabled INTEGER DEFAULT 1
      )
    ''');

    await db.execute('''
      CREATE TABLE recent_plays (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        songId TEXT NOT NULL,
        playedAt INTEGER NOT NULL,
        FOREIGN KEY (songId) REFERENCES songs (id) ON DELETE CASCADE
      )
    ''');

    await db.execute('CREATE INDEX idx_songs_artist ON songs (artist)');
    await db.execute('CREATE INDEX idx_songs_album ON songs (album)');
    await db.execute('CREATE INDEX idx_songs_title ON songs (title)');
    await db.execute('CREATE INDEX idx_playlist_songs_playlist ON playlist_songs (playlistId)');
    await db.execute('CREATE INDEX idx_recent_plays_song ON recent_plays (songId)');
  }

  Future<void> _onUpgrade(Database db, int oldVersion, int newVersion) async {
    // Handle database migrations here
  }

  // Song operations
  Future<void> insertSong(Song song) async {
    final db = await database;
    await db.insert(
      'songs',
      song.toMap(),
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<void> insertSongs(List<Song> songs) async {
    final db = await database;
    final batch = db.batch();
    for (final song in songs) {
      batch.insert(
        'songs',
        song.toMap(),
        conflictAlgorithm: ConflictAlgorithm.replace,
      );
    }
    await batch.commit(noResult: true);
  }

  Future<List<Song>> getAllSongs() async {
    final db = await database;
    final maps = await db.query('songs', orderBy: 'title ASC');
    return maps.map((map) => Song.fromMap(map)).toList();
  }

  Future<Song?> getSongById(String id) async {
    final db = await database;
    final maps = await db.query(
      'songs',
      where: 'id = ?',
      whereArgs: [id],
    );
    if (maps.isEmpty) return null;
    return Song.fromMap(maps.first);
  }

  Future<List<Song>> getSongsByAlbum(String album, String artist) async {
    final db = await database;
    final maps = await db.query(
      'songs',
      where: 'album = ? AND artist = ?',
      whereArgs: [album, artist],
      orderBy: 'trackNumber ASC, title ASC',
    );
    return maps.map((map) => Song.fromMap(map)).toList();
  }

  Future<List<Song>> getSongsByArtist(String artist) async {
    final db = await database;
    final maps = await db.query(
      'songs',
      where: 'artist = ?',
      whereArgs: [artist],
      orderBy: 'album ASC, trackNumber ASC',
    );
    return maps.map((map) => Song.fromMap(map)).toList();
  }

  Future<List<Song>> getFavoriteSongs() async {
    final db = await database;
    final maps = await db.query(
      'songs',
      where: 'isFavorite = 1',
      orderBy: 'title ASC',
    );
    return maps.map((map) => Song.fromMap(map)).toList();
  }

  Future<void> updateSong(Song song) async {
    final db = await database;
    await db.update(
      'songs',
      song.toMap(),
      where: 'id = ?',
      whereArgs: [song.id],
    );
  }

  Future<void> toggleFavorite(String songId, bool isFavorite) async {
    final db = await database;
    await db.update(
      'songs',
      {'isFavorite': isFavorite ? 1 : 0},
      where: 'id = ?',
      whereArgs: [songId],
    );
  }

  Future<void> incrementPlayCount(String songId) async {
    final db = await database;
    await db.rawUpdate('''
      UPDATE songs
      SET playCount = playCount + 1, lastPlayed = ?
      WHERE id = ?
    ''', [DateTime.now().millisecondsSinceEpoch, songId]);
  }

  Future<void> deleteSong(String id) async {
    final db = await database;
    await db.delete('songs', where: 'id = ?', whereArgs: [id]);
  }

  Future<void> deleteAllSongs() async {
    final db = await database;
    await db.delete('songs');
  }

  // Playlist operations
  Future<void> insertPlaylist(Playlist playlist) async {
    final db = await database;
    await db.insert(
      'playlists',
      playlist.toMap(),
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<List<Playlist>> getAllPlaylists() async {
    final db = await database;
    final maps = await db.query('playlists', orderBy: 'updatedAt DESC');

    final playlists = <Playlist>[];
    for (final map in maps) {
      final songs = await getPlaylistSongs(map['id'] as String);
      playlists.add(Playlist.fromMap(map, songs: songs));
    }
    return playlists;
  }

  Future<Playlist?> getPlaylistById(String id) async {
    final db = await database;
    final maps = await db.query(
      'playlists',
      where: 'id = ?',
      whereArgs: [id],
    );
    if (maps.isEmpty) return null;
    final songs = await getPlaylistSongs(id);
    return Playlist.fromMap(maps.first, songs: songs);
  }

  Future<List<Song>> getPlaylistSongs(String playlistId) async {
    final db = await database;
    final maps = await db.rawQuery('''
      SELECT s.* FROM songs s
      INNER JOIN playlist_songs ps ON s.id = ps.songId
      WHERE ps.playlistId = ?
      ORDER BY ps.position ASC
    ''', [playlistId]);
    return maps.map((map) => Song.fromMap(map)).toList();
  }

  Future<void> addSongToPlaylist(String playlistId, String songId) async {
    final db = await database;
    final result = await db.rawQuery(
      'SELECT MAX(position) as maxPos FROM playlist_songs WHERE playlistId = ?',
      [playlistId],
    );
    final maxPos = (result.first['maxPos'] as int?) ?? -1;

    await db.insert(
      'playlist_songs',
      {
        'playlistId': playlistId,
        'songId': songId,
        'position': maxPos + 1,
      },
      conflictAlgorithm: ConflictAlgorithm.ignore,
    );

    await db.update(
      'playlists',
      {'updatedAt': DateTime.now().millisecondsSinceEpoch},
      where: 'id = ?',
      whereArgs: [playlistId],
    );
  }

  Future<void> removeSongFromPlaylist(String playlistId, String songId) async {
    final db = await database;
    await db.delete(
      'playlist_songs',
      where: 'playlistId = ? AND songId = ?',
      whereArgs: [playlistId, songId],
    );
  }

  Future<void> updatePlaylist(Playlist playlist) async {
    final db = await database;
    await db.update(
      'playlists',
      playlist.toMap(),
      where: 'id = ?',
      whereArgs: [playlist.id],
    );
  }

  Future<void> deletePlaylist(String id) async {
    final db = await database;
    await db.delete('playlists', where: 'id = ?', whereArgs: [id]);
    await db.delete('playlist_songs', where: 'playlistId = ?', whereArgs: [id]);
  }

  // Music folder operations
  Future<void> insertMusicFolder(MusicFolder folder) async {
    final db = await database;
    await db.insert(
      'music_folders',
      folder.toMap(),
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<List<MusicFolder>> getAllMusicFolders() async {
    final db = await database;
    final maps = await db.query('music_folders', orderBy: 'name ASC');
    return maps.map((map) => MusicFolder.fromMap(map)).toList();
  }

  Future<void> updateMusicFolder(MusicFolder folder) async {
    final db = await database;
    await db.update(
      'music_folders',
      folder.toMap(),
      where: 'id = ?',
      whereArgs: [folder.id],
    );
  }

  Future<void> deleteMusicFolder(String id) async {
    final db = await database;
    await db.delete('music_folders', where: 'id = ?', whereArgs: [id]);
  }

  // Recent plays operations
  Future<void> addRecentPlay(String songId) async {
    final db = await database;
    await db.insert('recent_plays', {
      'songId': songId,
      'playedAt': DateTime.now().millisecondsSinceEpoch,
    });

    // Keep only last 100 recent plays
    await db.rawDelete('''
      DELETE FROM recent_plays
      WHERE id NOT IN (
        SELECT id FROM recent_plays ORDER BY playedAt DESC LIMIT 100
      )
    ''');
  }

  Future<List<Song>> getRecentlyPlayed({int limit = 20}) async {
    final db = await database;
    final maps = await db.rawQuery('''
      SELECT s.* FROM songs s
      INNER JOIN (
        SELECT songId, MAX(playedAt) as lastPlayed
        FROM recent_plays
        GROUP BY songId
        ORDER BY lastPlayed DESC
        LIMIT ?
      ) rp ON s.id = rp.songId
      ORDER BY rp.lastPlayed DESC
    ''', [limit]);
    return maps.map((map) => Song.fromMap(map)).toList();
  }

  Future<List<Song>> getMostPlayed({int limit = 20}) async {
    final db = await database;
    final maps = await db.query(
      'songs',
      where: 'playCount > 0',
      orderBy: 'playCount DESC',
      limit: limit,
    );
    return maps.map((map) => Song.fromMap(map)).toList();
  }

  // Search operations
  Future<List<Song>> searchSongs(String query) async {
    final db = await database;
    final searchQuery = '%$query%';
    final maps = await db.query(
      'songs',
      where: 'title LIKE ? OR artist LIKE ? OR album LIKE ?',
      whereArgs: [searchQuery, searchQuery, searchQuery],
      orderBy: 'title ASC',
      limit: 50,
    );
    return maps.map((map) => Song.fromMap(map)).toList();
  }

  // Stats
  Future<Map<String, int>> getLibraryStats() async {
    final db = await database;
    final songCount = Sqflite.firstIntValue(
      await db.rawQuery('SELECT COUNT(*) FROM songs'),
    );
    final artistCount = Sqflite.firstIntValue(
      await db.rawQuery('SELECT COUNT(DISTINCT artist) FROM songs'),
    );
    final albumCount = Sqflite.firstIntValue(
      await db.rawQuery('SELECT COUNT(DISTINCT album || artist) FROM songs'),
    );
    final playlistCount = Sqflite.firstIntValue(
      await db.rawQuery('SELECT COUNT(*) FROM playlists'),
    );

    return {
      'songs': songCount ?? 0,
      'artists': artistCount ?? 0,
      'albums': albumCount ?? 0,
      'playlists': playlistCount ?? 0,
    };
  }

  Future<void> close() async {
    final db = await database;
    await db.close();
    _database = null;
  }
}
