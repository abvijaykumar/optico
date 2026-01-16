import 'dart:typed_data';
import 'song.dart';

class Album {
  final String id;
  final String name;
  final String artist;
  final int? year;
  final Uint8List? albumArt;
  final String? albumArtPath;
  final List<Song> songs;

  Album({
    required this.id,
    required this.name,
    required this.artist,
    this.year,
    this.albumArt,
    this.albumArtPath,
    this.songs = const [],
  });

  String get displayName => name.isEmpty ? 'Unknown Album' : name;
  String get displayArtist => artist.isEmpty ? 'Unknown Artist' : artist;

  int get songCount => songs.length;

  Duration get totalDuration {
    return songs.fold(
      Duration.zero,
      (total, song) => total + song.duration,
    );
  }

  String get totalDurationString {
    final totalMinutes = totalDuration.inMinutes;
    if (totalMinutes >= 60) {
      final hours = totalMinutes ~/ 60;
      final minutes = totalMinutes % 60;
      return '$hours hr ${minutes} min';
    }
    return '$totalMinutes min';
  }

  Album copyWith({
    String? id,
    String? name,
    String? artist,
    int? year,
    Uint8List? albumArt,
    String? albumArtPath,
    List<Song>? songs,
  }) {
    return Album(
      id: id ?? this.id,
      name: name ?? this.name,
      artist: artist ?? this.artist,
      year: year ?? this.year,
      albumArt: albumArt ?? this.albumArt,
      albumArtPath: albumArtPath ?? this.albumArtPath,
      songs: songs ?? this.songs,
    );
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is Album && other.id == id;
  }

  @override
  int get hashCode => id.hashCode;

  @override
  String toString() {
    return 'Album(id: $id, name: $name, artist: $artist, songs: ${songs.length})';
  }
}
