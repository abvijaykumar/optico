import 'dart:io';
import 'dart:typed_data';
import 'package:flutter_media_metadata/flutter_media_metadata.dart';
import 'package:path/path.dart' as p;
import 'package:uuid/uuid.dart';
import '../models/models.dart';

class MusicScannerService {
  static const List<String> supportedExtensions = [
    '.mp3',
    '.m4a',
    '.aac',
    '.flac',
    '.wav',
    '.ogg',
    '.wma',
    '.opus',
    '.alac',
    '.aiff',
  ];

  final _uuid = const Uuid();

  Future<List<Song>> scanFolder(String folderPath) async {
    final songs = <Song>[];
    final directory = Directory(folderPath);

    if (!await directory.exists()) {
      return songs;
    }

    await for (final entity in directory.list(recursive: true)) {
      if (entity is File) {
        final extension = p.extension(entity.path).toLowerCase();
        if (supportedExtensions.contains(extension)) {
          final song = await _extractSongMetadata(entity.path);
          if (song != null) {
            songs.add(song);
          }
        }
      }
    }

    return songs;
  }

  Future<Song?> _extractSongMetadata(String filePath) async {
    try {
      final file = File(filePath);
      final metadata = await MetadataRetriever.fromFile(file);

      final fileName = p.basenameWithoutExtension(filePath);
      final extension = p.extension(filePath).toLowerCase().replaceFirst('.', '');

      // Try to extract album art
      Uint8List? albumArt;
      if (metadata.albumArt != null) {
        albumArt = metadata.albumArt;
      }

      return Song(
        id: _uuid.v4(),
        title: metadata.trackName ?? fileName,
        artist: metadata.albumArtistName ?? metadata.trackArtistNames?.join(', ') ?? 'Unknown Artist',
        album: metadata.albumName ?? 'Unknown Album',
        albumArtist: metadata.albumArtistName ?? '',
        filePath: filePath,
        duration: Duration(milliseconds: metadata.trackDuration ?? 0),
        trackNumber: metadata.trackNumber ?? 0,
        genre: metadata.genre,
        year: metadata.year,
        bitrate: metadata.bitrate,
        format: extension,
        albumArt: albumArt,
        dateAdded: DateTime.now(),
      );
    } catch (e) {
      // If metadata extraction fails, create a basic song entry
      try {
        final fileName = p.basenameWithoutExtension(filePath);
        final extension = p.extension(filePath).toLowerCase().replaceFirst('.', '');

        return Song(
          id: _uuid.v4(),
          title: fileName,
          artist: 'Unknown Artist',
          album: 'Unknown Album',
          filePath: filePath,
          duration: Duration.zero,
          format: extension,
          dateAdded: DateTime.now(),
        );
      } catch (_) {
        return null;
      }
    }
  }

  Future<List<Song>> scanMultipleFolders(List<MusicFolder> folders) async {
    final allSongs = <Song>[];

    for (final folder in folders) {
      if (folder.isEnabled) {
        final songs = await scanFolder(folder.path);
        allSongs.addAll(songs);
      }
    }

    return allSongs;
  }

  bool isAudioFile(String filePath) {
    final extension = p.extension(filePath).toLowerCase();
    return supportedExtensions.contains(extension);
  }

  Future<int> countAudioFiles(String folderPath) async {
    int count = 0;
    final directory = Directory(folderPath);

    if (!await directory.exists()) {
      return count;
    }

    await for (final entity in directory.list(recursive: true)) {
      if (entity is File) {
        final extension = p.extension(entity.path).toLowerCase();
        if (supportedExtensions.contains(extension)) {
          count++;
        }
      }
    }

    return count;
  }
}
