import 'dart:typed_data';
import 'song.dart';

class Playlist {
  final String id;
  final String name;
  final String? description;
  final Uint8List? coverImage;
  final String? coverImagePath;
  final List<Song> songs;
  final DateTime createdAt;
  final DateTime updatedAt;
  final bool isSystemPlaylist;

  Playlist({
    required this.id,
    required this.name,
    this.description,
    this.coverImage,
    this.coverImagePath,
    this.songs = const [],
    required this.createdAt,
    required this.updatedAt,
    this.isSystemPlaylist = false,
  });

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

  Playlist copyWith({
    String? id,
    String? name,
    String? description,
    Uint8List? coverImage,
    String? coverImagePath,
    List<Song>? songs,
    DateTime? createdAt,
    DateTime? updatedAt,
    bool? isSystemPlaylist,
  }) {
    return Playlist(
      id: id ?? this.id,
      name: name ?? this.name,
      description: description ?? this.description,
      coverImage: coverImage ?? this.coverImage,
      coverImagePath: coverImagePath ?? this.coverImagePath,
      songs: songs ?? this.songs,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      isSystemPlaylist: isSystemPlaylist ?? this.isSystemPlaylist,
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'name': name,
      'description': description,
      'coverImagePath': coverImagePath,
      'createdAt': createdAt.millisecondsSinceEpoch,
      'updatedAt': updatedAt.millisecondsSinceEpoch,
      'isSystemPlaylist': isSystemPlaylist ? 1 : 0,
    };
  }

  factory Playlist.fromMap(Map<String, dynamic> map, {List<Song>? songs}) {
    return Playlist(
      id: map['id'] as String,
      name: map['name'] as String,
      description: map['description'] as String?,
      coverImagePath: map['coverImagePath'] as String?,
      songs: songs ?? const [],
      createdAt: DateTime.fromMillisecondsSinceEpoch(map['createdAt'] as int),
      updatedAt: DateTime.fromMillisecondsSinceEpoch(map['updatedAt'] as int),
      isSystemPlaylist: map['isSystemPlaylist'] == 1,
    );
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is Playlist && other.id == id;
  }

  @override
  int get hashCode => id.hashCode;

  @override
  String toString() {
    return 'Playlist(id: $id, name: $name, songs: ${songs.length})';
  }
}
