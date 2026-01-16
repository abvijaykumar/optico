import 'package:flutter/foundation.dart';
import 'package:collection/collection.dart';
import '../models/models.dart';
import '../services/services.dart';

class LibraryProvider extends ChangeNotifier {
  final DatabaseService _databaseService;
  final MusicScannerService _scannerService;

  List<Song> _songs = [];
  List<Album> _albums = [];
  List<Artist> _artists = [];
  List<Playlist> _playlists = [];
  List<MusicFolder> _folders = [];
  List<Song> _recentlyPlayed = [];
  List<Song> _mostPlayed = [];
  List<Song> _favoriteSongs = [];
  Map<String, int> _stats = {};

  bool _isLoading = false;
  bool _isScanning = false;
  String _scanningStatus = '';
  double _scanProgress = 0;

  // Getters
  List<Song> get songs => _songs;
  List<Album> get albums => _albums;
  List<Artist> get artists => _artists;
  List<Playlist> get playlists => _playlists;
  List<MusicFolder> get folders => _folders;
  List<Song> get recentlyPlayed => _recentlyPlayed;
  List<Song> get mostPlayed => _mostPlayed;
  List<Song> get favoriteSongs => _favoriteSongs;
  Map<String, int> get stats => _stats;
  bool get isLoading => _isLoading;
  bool get isScanning => _isScanning;
  String get scanningStatus => _scanningStatus;
  double get scanProgress => _scanProgress;

  LibraryProvider({
    required DatabaseService databaseService,
    required MusicScannerService scannerService,
  })  : _databaseService = databaseService,
        _scannerService = scannerService;

  Future<void> initialize() async {
    _isLoading = true;
    notifyListeners();

    await loadLibrary();
    await loadFolders();
    await loadPlaylists();
    await loadRecentlyPlayed();
    await loadMostPlayed();
    await loadFavorites();
    await loadStats();

    _isLoading = false;
    notifyListeners();
  }

  Future<void> loadLibrary() async {
    _songs = await _databaseService.getAllSongs();
    _organizeLibrary();
    notifyListeners();
  }

  void _organizeLibrary() {
    // Organize songs into albums
    final albumMap = <String, Album>{};
    for (final song in _songs) {
      final key = '${song.album}|||${song.artist}';
      if (!albumMap.containsKey(key)) {
        albumMap[key] = Album(
          id: key,
          name: song.album,
          artist: song.artist,
          year: song.year,
          albumArt: song.albumArt,
          albumArtPath: song.albumArtPath,
          songs: [],
        );
      }
      albumMap[key] = albumMap[key]!.copyWith(
        songs: [...albumMap[key]!.songs, song],
      );
    }
    _albums = albumMap.values.toList()
      ..sort((a, b) => a.name.toLowerCase().compareTo(b.name.toLowerCase()));

    // Organize songs into artists
    final artistMap = <String, Artist>{};
    for (final song in _songs) {
      final artistName = song.artist;
      if (!artistMap.containsKey(artistName)) {
        artistMap[artistName] = Artist(
          id: artistName,
          name: artistName,
          songs: [],
          albums: [],
        );
      }
      artistMap[artistName] = artistMap[artistName]!.copyWith(
        songs: [...artistMap[artistName]!.songs, song],
      );
    }

    // Add albums to artists
    for (final album in _albums) {
      final artistName = album.artist;
      if (artistMap.containsKey(artistName)) {
        artistMap[artistName] = artistMap[artistName]!.copyWith(
          albums: [...artistMap[artistName]!.albums, album],
        );
      }
    }

    _artists = artistMap.values.toList()
      ..sort((a, b) => a.name.toLowerCase().compareTo(b.name.toLowerCase()));
  }

  Future<void> loadFolders() async {
    _folders = await _databaseService.getAllMusicFolders();
    notifyListeners();
  }

  Future<void> loadPlaylists() async {
    _playlists = await _databaseService.getAllPlaylists();
    notifyListeners();
  }

  Future<void> loadRecentlyPlayed() async {
    _recentlyPlayed = await _databaseService.getRecentlyPlayed(limit: 20);
    notifyListeners();
  }

  Future<void> loadMostPlayed() async {
    _mostPlayed = await _databaseService.getMostPlayed(limit: 20);
    notifyListeners();
  }

  Future<void> loadFavorites() async {
    _favoriteSongs = await _databaseService.getFavoriteSongs();
    notifyListeners();
  }

  Future<void> loadStats() async {
    _stats = await _databaseService.getLibraryStats();
    notifyListeners();
  }

  // Folder management
  Future<void> addFolder(String path) async {
    final folderName = path.split('/').last;
    final folder = MusicFolder(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      path: path,
      name: folderName,
    );

    await _databaseService.insertMusicFolder(folder);
    await loadFolders();

    // Scan the new folder
    await scanFolder(folder);
  }

  Future<void> removeFolder(String folderId) async {
    await _databaseService.deleteMusicFolder(folderId);
    await loadFolders();
  }

  Future<void> toggleFolderEnabled(String folderId, bool enabled) async {
    final folder = _folders.firstWhereOrNull((f) => f.id == folderId);
    if (folder != null) {
      await _databaseService.updateMusicFolder(
        folder.copyWith(isEnabled: enabled),
      );
      await loadFolders();
    }
  }

  Future<void> scanFolder(MusicFolder folder) async {
    _isScanning = true;
    _scanningStatus = 'Scanning ${folder.name}...';
    _scanProgress = 0;
    notifyListeners();

    try {
      final songs = await _scannerService.scanFolder(folder.path);

      // Save songs to database
      await _databaseService.insertSongs(songs);

      // Update folder with song count
      await _databaseService.updateMusicFolder(
        folder.copyWith(
          songCount: songs.length,
          lastScanned: DateTime.now(),
        ),
      );

      await loadLibrary();
      await loadFolders();
      await loadStats();
    } finally {
      _isScanning = false;
      _scanningStatus = '';
      _scanProgress = 0;
      notifyListeners();
    }
  }

  Future<void> scanAllFolders() async {
    _isScanning = true;
    notifyListeners();

    try {
      for (int i = 0; i < _folders.length; i++) {
        final folder = _folders[i];
        if (folder.isEnabled) {
          _scanningStatus = 'Scanning ${folder.name}...';
          _scanProgress = i / _folders.length;
          notifyListeners();

          await scanFolder(folder);
        }
      }
    } finally {
      _isScanning = false;
      _scanningStatus = '';
      _scanProgress = 0;
      notifyListeners();
    }
  }

  // Playlist management
  Future<Playlist> createPlaylist(String name, {String? description}) async {
    final now = DateTime.now();
    final playlist = Playlist(
      id: now.millisecondsSinceEpoch.toString(),
      name: name,
      description: description,
      createdAt: now,
      updatedAt: now,
    );

    await _databaseService.insertPlaylist(playlist);
    await loadPlaylists();
    return playlist;
  }

  Future<void> deletePlaylist(String playlistId) async {
    await _databaseService.deletePlaylist(playlistId);
    await loadPlaylists();
  }

  Future<void> updatePlaylist(Playlist playlist) async {
    await _databaseService.updatePlaylist(
      playlist.copyWith(updatedAt: DateTime.now()),
    );
    await loadPlaylists();
  }

  Future<void> addSongToPlaylist(String playlistId, String songId) async {
    await _databaseService.addSongToPlaylist(playlistId, songId);
    await loadPlaylists();
  }

  Future<void> removeSongFromPlaylist(String playlistId, String songId) async {
    await _databaseService.removeSongFromPlaylist(playlistId, songId);
    await loadPlaylists();
  }

  // Song operations
  Future<void> toggleFavorite(Song song) async {
    final newFavoriteStatus = !song.isFavorite;
    await _databaseService.toggleFavorite(song.id, newFavoriteStatus);

    // Update local state
    final index = _songs.indexWhere((s) => s.id == song.id);
    if (index != -1) {
      _songs[index] = _songs[index].copyWith(isFavorite: newFavoriteStatus);
    }

    await loadFavorites();
    notifyListeners();
  }

  Future<void> recordSongPlay(Song song) async {
    await _databaseService.incrementPlayCount(song.id);
    await _databaseService.addRecentPlay(song.id);
    await loadRecentlyPlayed();
    await loadMostPlayed();
  }

  // Search
  Future<List<Song>> searchSongs(String query) async {
    if (query.isEmpty) return [];
    return await _databaseService.searchSongs(query);
  }

  List<Album> searchAlbums(String query) {
    if (query.isEmpty) return [];
    final lowerQuery = query.toLowerCase();
    return _albums
        .where((album) =>
            album.name.toLowerCase().contains(lowerQuery) ||
            album.artist.toLowerCase().contains(lowerQuery))
        .toList();
  }

  List<Artist> searchArtists(String query) {
    if (query.isEmpty) return [];
    final lowerQuery = query.toLowerCase();
    return _artists
        .where((artist) => artist.name.toLowerCase().contains(lowerQuery))
        .toList();
  }

  // Get songs by album
  List<Song> getSongsByAlbum(Album album) {
    return _songs
        .where((s) => s.album == album.name && s.artist == album.artist)
        .toList()
      ..sort((a, b) {
        final trackCompare = a.trackNumber.compareTo(b.trackNumber);
        if (trackCompare != 0) return trackCompare;
        return a.title.compareTo(b.title);
      });
  }

  // Get songs by artist
  List<Song> getSongsByArtist(Artist artist) {
    return _songs.where((s) => s.artist == artist.name).toList()
      ..sort((a, b) => a.title.compareTo(b.title));
  }

  // Get albums by artist
  List<Album> getAlbumsByArtist(Artist artist) {
    return _albums.where((a) => a.artist == artist.name).toList();
  }
}
