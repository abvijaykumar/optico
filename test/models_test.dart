import 'package:flutter_test/flutter_test.dart';
import 'package:optico/models/models.dart';
import 'package:optico/services/audio_player_service.dart';

void main() {
  group('Song model', () {
    test('creates song with required fields', () {
      final song = Song(
        id: '1',
        title: 'Test Song',
        artist: 'Test Artist',
        album: 'Test Album',
        filePath: '/path/to/song.mp3',
        duration: const Duration(minutes: 3, seconds: 30),
      );

      expect(song.id, '1');
      expect(song.title, 'Test Song');
      expect(song.artist, 'Test Artist');
      expect(song.album, 'Test Album');
      expect(song.filePath, '/path/to/song.mp3');
      expect(song.duration.inSeconds, 210);
    });

    test('durationString formats correctly', () {
      final song = Song(
        id: '1',
        title: 'Test',
        artist: 'Artist',
        album: 'Album',
        filePath: '/test.mp3',
        duration: const Duration(minutes: 3, seconds: 5),
      );

      expect(song.durationString, '3:05');
    });

    test('displayTitle returns filename when title is empty', () {
      final song = Song(
        id: '1',
        title: '',
        artist: 'Artist',
        album: 'Album',
        filePath: '/path/to/my_song.mp3',
        duration: Duration.zero,
      );

      expect(song.displayTitle, 'my_song.mp3');
    });

    test('displayArtist returns Unknown Artist when empty', () {
      final song = Song(
        id: '1',
        title: 'Song',
        artist: '',
        album: 'Album',
        filePath: '/test.mp3',
        duration: Duration.zero,
      );

      expect(song.displayArtist, 'Unknown Artist');
    });

    test('copyWith creates new instance with changed fields', () {
      final song = Song(
        id: '1',
        title: 'Original',
        artist: 'Artist',
        album: 'Album',
        filePath: '/test.mp3',
        duration: Duration.zero,
        isFavorite: false,
      );

      final updated = song.copyWith(title: 'Updated', isFavorite: true);

      expect(updated.title, 'Updated');
      expect(updated.isFavorite, true);
      expect(updated.artist, 'Artist'); // unchanged
      expect(updated.id, '1'); // unchanged
    });

    test('toMap and fromMap roundtrip', () {
      final song = Song(
        id: '1',
        title: 'Test Song',
        artist: 'Test Artist',
        album: 'Test Album',
        filePath: '/path/to/test.mp3',
        duration: const Duration(minutes: 4, seconds: 20),
        trackNumber: 3,
        genre: 'Rock',
        year: 2023,
        isFavorite: true,
        playCount: 5,
      );

      final map = song.toMap();
      final restored = Song.fromMap(map);

      expect(restored.id, song.id);
      expect(restored.title, song.title);
      expect(restored.artist, song.artist);
      expect(restored.album, song.album);
      expect(restored.filePath, song.filePath);
      expect(restored.duration, song.duration);
      expect(restored.trackNumber, song.trackNumber);
      expect(restored.genre, song.genre);
      expect(restored.year, song.year);
      expect(restored.isFavorite, song.isFavorite);
      expect(restored.playCount, song.playCount);
    });

    test('equality based on id', () {
      final song1 = Song(
        id: '1',
        title: 'Song A',
        artist: 'Artist',
        album: 'Album',
        filePath: '/a.mp3',
        duration: Duration.zero,
      );

      final song2 = Song(
        id: '1',
        title: 'Song B',
        artist: 'Other',
        album: 'Other',
        filePath: '/b.mp3',
        duration: Duration.zero,
      );

      expect(song1, equals(song2));
    });
  });

  group('Album model', () {
    test('calculates song count and total duration', () {
      final songs = [
        Song(
          id: '1',
          title: 'Song 1',
          artist: 'Artist',
          album: 'Album',
          filePath: '/1.mp3',
          duration: const Duration(minutes: 3),
        ),
        Song(
          id: '2',
          title: 'Song 2',
          artist: 'Artist',
          album: 'Album',
          filePath: '/2.mp3',
          duration: const Duration(minutes: 4),
        ),
      ];

      final album = Album(
        id: 'a1',
        name: 'Test Album',
        artist: 'Test Artist',
        songs: songs,
      );

      expect(album.songCount, 2);
      expect(album.totalDuration, const Duration(minutes: 7));
      expect(album.totalDurationString, '7 min');
    });

    test('totalDurationString shows hours for long albums', () {
      final songs = List.generate(
        20,
        (i) => Song(
          id: '$i',
          title: 'Song $i',
          artist: 'Artist',
          album: 'Album',
          filePath: '/$i.mp3',
          duration: const Duration(minutes: 5),
        ),
      );

      final album = Album(
        id: 'a1',
        name: 'Long Album',
        artist: 'Artist',
        songs: songs,
      );

      expect(album.totalDurationString, '1 hr 40 min');
    });
  });

  group('Playlist model', () {
    test('toMap and fromMap roundtrip', () {
      final playlist = Playlist(
        id: 'p1',
        name: 'My Playlist',
        description: 'Test description',
        createdAt: DateTime(2024, 1, 15),
        updatedAt: DateTime(2024, 1, 20),
      );

      final map = playlist.toMap();
      final restored = Playlist.fromMap(map);

      expect(restored.id, playlist.id);
      expect(restored.name, playlist.name);
      expect(restored.description, playlist.description);
    });
  });

  group('MusicFolder model', () {
    test('toMap and fromMap roundtrip', () {
      final folder = MusicFolder(
        id: 'f1',
        path: '/storage/emulated/0/Music',
        name: 'Music',
        songCount: 42,
        isEnabled: true,
      );

      final map = folder.toMap();
      final restored = MusicFolder.fromMap(map);

      expect(restored.id, folder.id);
      expect(restored.path, folder.path);
      expect(restored.name, folder.name);
      expect(restored.songCount, folder.songCount);
      expect(restored.isEnabled, folder.isEnabled);
    });
  });

  group('Audio enums', () {
    test('RepeatMode values', () {
      expect(RepeatMode.values.length, 3);
      expect(RepeatMode.off.index, 0);
      expect(RepeatMode.one.index, 1);
      expect(RepeatMode.all.index, 2);
    });

    test('ShuffleMode values', () {
      expect(ShuffleMode.values.length, 2);
      expect(ShuffleMode.off.index, 0);
      expect(ShuffleMode.on.index, 1);
    });
  });
}
