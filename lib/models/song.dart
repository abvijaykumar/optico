import 'dart:typed_data';

class Song {
  final String id;
  final String title;
  final String artist;
  final String album;
  final String albumArtist;
  final String filePath;
  final Duration duration;
  final int trackNumber;
  final String? genre;
  final int? year;
  final int? bitrate;
  final int? sampleRate;
  final String? format;
  final Uint8List? albumArt;
  final String? albumArtPath;
  final DateTime? dateAdded;
  final DateTime? lastPlayed;
  final int playCount;
  final bool isFavorite;

  Song({
    required this.id,
    required this.title,
    required this.artist,
    required this.album,
    this.albumArtist = '',
    required this.filePath,
    required this.duration,
    this.trackNumber = 0,
    this.genre,
    this.year,
    this.bitrate,
    this.sampleRate,
    this.format,
    this.albumArt,
    this.albumArtPath,
    this.dateAdded,
    this.lastPlayed,
    this.playCount = 0,
    this.isFavorite = false,
  });

  String get durationString {
    final minutes = duration.inMinutes;
    final seconds = duration.inSeconds % 60;
    return '$minutes:${seconds.toString().padLeft(2, '0')}';
  }

  String get displayArtist => artist.isEmpty ? 'Unknown Artist' : artist;
  String get displayAlbum => album.isEmpty ? 'Unknown Album' : album;
  String get displayTitle => title.isEmpty ? filePath.split('/').last : title;

  Song copyWith({
    String? id,
    String? title,
    String? artist,
    String? album,
    String? albumArtist,
    String? filePath,
    Duration? duration,
    int? trackNumber,
    String? genre,
    int? year,
    int? bitrate,
    int? sampleRate,
    String? format,
    Uint8List? albumArt,
    String? albumArtPath,
    DateTime? dateAdded,
    DateTime? lastPlayed,
    int? playCount,
    bool? isFavorite,
  }) {
    return Song(
      id: id ?? this.id,
      title: title ?? this.title,
      artist: artist ?? this.artist,
      album: album ?? this.album,
      albumArtist: albumArtist ?? this.albumArtist,
      filePath: filePath ?? this.filePath,
      duration: duration ?? this.duration,
      trackNumber: trackNumber ?? this.trackNumber,
      genre: genre ?? this.genre,
      year: year ?? this.year,
      bitrate: bitrate ?? this.bitrate,
      sampleRate: sampleRate ?? this.sampleRate,
      format: format ?? this.format,
      albumArt: albumArt ?? this.albumArt,
      albumArtPath: albumArtPath ?? this.albumArtPath,
      dateAdded: dateAdded ?? this.dateAdded,
      lastPlayed: lastPlayed ?? this.lastPlayed,
      playCount: playCount ?? this.playCount,
      isFavorite: isFavorite ?? this.isFavorite,
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'title': title,
      'artist': artist,
      'album': album,
      'albumArtist': albumArtist,
      'filePath': filePath,
      'duration': duration.inMilliseconds,
      'trackNumber': trackNumber,
      'genre': genre,
      'year': year,
      'bitrate': bitrate,
      'sampleRate': sampleRate,
      'format': format,
      'albumArtPath': albumArtPath,
      'dateAdded': dateAdded?.millisecondsSinceEpoch,
      'lastPlayed': lastPlayed?.millisecondsSinceEpoch,
      'playCount': playCount,
      'isFavorite': isFavorite ? 1 : 0,
    };
  }

  factory Song.fromMap(Map<String, dynamic> map) {
    return Song(
      id: map['id'] as String,
      title: map['title'] as String,
      artist: map['artist'] as String,
      album: map['album'] as String,
      albumArtist: map['albumArtist'] as String? ?? '',
      filePath: map['filePath'] as String,
      duration: Duration(milliseconds: map['duration'] as int),
      trackNumber: map['trackNumber'] as int? ?? 0,
      genre: map['genre'] as String?,
      year: map['year'] as int?,
      bitrate: map['bitrate'] as int?,
      sampleRate: map['sampleRate'] as int?,
      format: map['format'] as String?,
      albumArtPath: map['albumArtPath'] as String?,
      dateAdded: map['dateAdded'] != null
          ? DateTime.fromMillisecondsSinceEpoch(map['dateAdded'] as int)
          : null,
      lastPlayed: map['lastPlayed'] != null
          ? DateTime.fromMillisecondsSinceEpoch(map['lastPlayed'] as int)
          : null,
      playCount: map['playCount'] as int? ?? 0,
      isFavorite: map['isFavorite'] == 1,
    );
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is Song && other.id == id;
  }

  @override
  int get hashCode => id.hashCode;

  @override
  String toString() {
    return 'Song(id: $id, title: $title, artist: $artist, album: $album)';
  }
}
