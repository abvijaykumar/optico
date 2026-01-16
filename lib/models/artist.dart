import 'dart:typed_data';
import 'album.dart';
import 'song.dart';

class Artist {
  final String id;
  final String name;
  final Uint8List? artistImage;
  final String? artistImagePath;
  final List<Album> albums;
  final List<Song> songs;

  Artist({
    required this.id,
    required this.name,
    this.artistImage,
    this.artistImagePath,
    this.albums = const [],
    this.songs = const [],
  });

  String get displayName => name.isEmpty ? 'Unknown Artist' : name;

  int get albumCount => albums.length;
  int get songCount => songs.length;

  Duration get totalDuration {
    return songs.fold(
      Duration.zero,
      (total, song) => total + song.duration,
    );
  }

  Artist copyWith({
    String? id,
    String? name,
    Uint8List? artistImage,
    String? artistImagePath,
    List<Album>? albums,
    List<Song>? songs,
  }) {
    return Artist(
      id: id ?? this.id,
      name: name ?? this.name,
      artistImage: artistImage ?? this.artistImage,
      artistImagePath: artistImagePath ?? this.artistImagePath,
      albums: albums ?? this.albums,
      songs: songs ?? this.songs,
    );
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is Artist && other.id == id;
  }

  @override
  int get hashCode => id.hashCode;

  @override
  String toString() {
    return 'Artist(id: $id, name: $name, albums: ${albums.length}, songs: ${songs.length})';
  }
}
