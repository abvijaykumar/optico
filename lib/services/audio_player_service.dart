import 'dart:math';
import 'package:just_audio/just_audio.dart';
import 'package:audio_session/audio_session.dart';
import 'package:rxdart/rxdart.dart';
import '../models/models.dart';

enum RepeatMode { off, one, all }

enum ShuffleMode { off, on }

class PositionData {
  final Duration position;
  final Duration bufferedPosition;
  final Duration duration;

  PositionData(this.position, this.bufferedPosition, this.duration);
}

class AudioPlayerService {
  final AudioPlayer _player = AudioPlayer();
  final _random = Random();

  List<Song> _queue = [];
  List<Song> _originalQueue = [];
  int _currentIndex = -1;
  Song? _currentSong;
  RepeatMode _repeatMode = RepeatMode.off;
  ShuffleMode _shuffleMode = ShuffleMode.off;

  // Stream controllers
  final _currentSongController = BehaviorSubject<Song?>();
  final _queueController = BehaviorSubject<List<Song>>.seeded([]);
  final _currentIndexController = BehaviorSubject<int>.seeded(-1);
  final _repeatModeController = BehaviorSubject<RepeatMode>.seeded(RepeatMode.off);
  final _shuffleModeController = BehaviorSubject<ShuffleMode>.seeded(ShuffleMode.off);

  // Getters for streams
  Stream<Song?> get currentSongStream => _currentSongController.stream;
  Stream<List<Song>> get queueStream => _queueController.stream;
  Stream<int> get currentIndexStream => _currentIndexController.stream;
  Stream<RepeatMode> get repeatModeStream => _repeatModeController.stream;
  Stream<ShuffleMode> get shuffleModeStream => _shuffleModeController.stream;
  Stream<PlayerState> get playerStateStream => _player.playerStateStream;
  Stream<Duration> get positionStream => _player.positionStream;
  Stream<Duration?> get durationStream => _player.durationStream;
  Stream<bool> get playingStream => _player.playingStream;

  Stream<PositionData> get positionDataStream =>
      Rx.combineLatest3<Duration, Duration, Duration?, PositionData>(
        _player.positionStream,
        _player.bufferedPositionStream,
        _player.durationStream,
        (position, bufferedPosition, duration) => PositionData(
          position,
          bufferedPosition,
          duration ?? Duration.zero,
        ),
      );

  // Getters for current state
  Song? get currentSong => _currentSong;
  List<Song> get queue => _queue;
  int get currentIndex => _currentIndex;
  RepeatMode get repeatMode => _repeatMode;
  ShuffleMode get shuffleMode => _shuffleMode;
  bool get isPlaying => _player.playing;
  Duration get position => _player.position;
  Duration get duration => _player.duration ?? Duration.zero;
  bool get hasNext => _currentIndex < _queue.length - 1 || _repeatMode == RepeatMode.all;
  bool get hasPrevious => _currentIndex > 0 || _repeatMode == RepeatMode.all;

  AudioPlayerService() {
    _initAudioSession();
    _setupPlayerListeners();
  }

  Future<void> _initAudioSession() async {
    final session = await AudioSession.instance;
    await session.configure(const AudioSessionConfiguration.music());
  }

  void _setupPlayerListeners() {
    _player.processingStateStream.listen((state) {
      if (state == ProcessingState.completed) {
        _handleSongComplete();
      }
    });
  }

  void _handleSongComplete() {
    switch (_repeatMode) {
      case RepeatMode.one:
        seek(Duration.zero);
        play();
        break;
      case RepeatMode.all:
        if (_currentIndex >= _queue.length - 1) {
          skipToIndex(0);
        } else {
          next();
        }
        break;
      case RepeatMode.off:
        if (_currentIndex < _queue.length - 1) {
          next();
        }
        break;
    }
  }

  Future<void> playSong(Song song) async {
    _currentSong = song;
    _currentSongController.add(song);

    try {
      await _player.setFilePath(song.filePath);
      await _player.play();
    } catch (e) {
      print('Error playing song: $e');
    }
  }

  Future<void> playQueue(List<Song> songs, {int startIndex = 0}) async {
    if (songs.isEmpty) return;

    _originalQueue = List.from(songs);
    _queue = List.from(songs);
    _queueController.add(_queue);

    if (_shuffleMode == ShuffleMode.on) {
      _shuffleQueue(keepCurrent: false, startIndex: startIndex);
    } else {
      _currentIndex = startIndex;
    }

    _currentIndexController.add(_currentIndex);
    await playSong(_queue[_currentIndex]);
  }

  Future<void> play() async {
    await _player.play();
  }

  Future<void> pause() async {
    await _player.pause();
  }

  Future<void> togglePlayPause() async {
    if (_player.playing) {
      await pause();
    } else {
      await play();
    }
  }

  Future<void> stop() async {
    await _player.stop();
    _currentSong = null;
    _currentSongController.add(null);
  }

  Future<void> seek(Duration position) async {
    await _player.seek(position);
  }

  Future<void> next() async {
    if (_queue.isEmpty) return;

    if (_repeatMode == RepeatMode.one) {
      seek(Duration.zero);
      play();
      return;
    }

    if (_currentIndex < _queue.length - 1) {
      _currentIndex++;
    } else if (_repeatMode == RepeatMode.all) {
      _currentIndex = 0;
    } else {
      return;
    }

    _currentIndexController.add(_currentIndex);
    await playSong(_queue[_currentIndex]);
  }

  Future<void> previous() async {
    if (_queue.isEmpty) return;

    // If more than 3 seconds into song, restart it
    if (_player.position.inSeconds > 3) {
      await seek(Duration.zero);
      return;
    }

    if (_currentIndex > 0) {
      _currentIndex--;
    } else if (_repeatMode == RepeatMode.all) {
      _currentIndex = _queue.length - 1;
    } else {
      await seek(Duration.zero);
      return;
    }

    _currentIndexController.add(_currentIndex);
    await playSong(_queue[_currentIndex]);
  }

  Future<void> skipToIndex(int index) async {
    if (index < 0 || index >= _queue.length) return;

    _currentIndex = index;
    _currentIndexController.add(_currentIndex);
    await playSong(_queue[_currentIndex]);
  }

  void toggleRepeatMode() {
    switch (_repeatMode) {
      case RepeatMode.off:
        _repeatMode = RepeatMode.all;
        break;
      case RepeatMode.all:
        _repeatMode = RepeatMode.one;
        break;
      case RepeatMode.one:
        _repeatMode = RepeatMode.off;
        break;
    }
    _repeatModeController.add(_repeatMode);
  }

  void toggleShuffleMode() {
    if (_shuffleMode == ShuffleMode.off) {
      _shuffleMode = ShuffleMode.on;
      _shuffleQueue(keepCurrent: true, startIndex: _currentIndex);
    } else {
      _shuffleMode = ShuffleMode.off;
      _unshuffleQueue();
    }
    _shuffleModeController.add(_shuffleMode);
  }

  void _shuffleQueue({required bool keepCurrent, required int startIndex}) {
    if (_originalQueue.isEmpty) return;

    final currentSong = keepCurrent && _currentIndex >= 0 && _currentIndex < _queue.length
        ? _queue[_currentIndex]
        : _originalQueue[startIndex];

    _queue = List.from(_originalQueue);
    _queue.shuffle(_random);

    // Move current song to front
    final currentSongIndex = _queue.indexWhere((s) => s.id == currentSong.id);
    if (currentSongIndex != -1) {
      _queue.removeAt(currentSongIndex);
      _queue.insert(0, currentSong);
    }

    _currentIndex = 0;
    _queueController.add(_queue);
    _currentIndexController.add(_currentIndex);
  }

  void _unshuffleQueue() {
    if (_originalQueue.isEmpty) return;

    final currentSong = _currentSong;
    _queue = List.from(_originalQueue);

    if (currentSong != null) {
      _currentIndex = _queue.indexWhere((s) => s.id == currentSong.id);
      if (_currentIndex == -1) _currentIndex = 0;
    }

    _queueController.add(_queue);
    _currentIndexController.add(_currentIndex);
  }

  void addToQueue(Song song) {
    _queue.add(song);
    _originalQueue.add(song);
    _queueController.add(_queue);
  }

  void addToQueueNext(Song song) {
    final insertIndex = _currentIndex + 1;
    _queue.insert(insertIndex, song);
    _originalQueue.add(song);
    _queueController.add(_queue);
  }

  void removeFromQueue(int index) {
    if (index < 0 || index >= _queue.length) return;

    final song = _queue[index];
    _queue.removeAt(index);
    _originalQueue.removeWhere((s) => s.id == song.id);

    if (index < _currentIndex) {
      _currentIndex--;
    } else if (index == _currentIndex && _currentIndex >= _queue.length) {
      _currentIndex = _queue.length - 1;
    }

    _queueController.add(_queue);
    _currentIndexController.add(_currentIndex);
  }

  void clearQueue() {
    _queue.clear();
    _originalQueue.clear();
    _currentIndex = -1;
    _currentSong = null;
    _queueController.add(_queue);
    _currentIndexController.add(_currentIndex);
    _currentSongController.add(null);
  }

  void reorderQueue(int oldIndex, int newIndex) {
    if (oldIndex < newIndex) {
      newIndex -= 1;
    }

    final song = _queue.removeAt(oldIndex);
    _queue.insert(newIndex, song);

    if (oldIndex == _currentIndex) {
      _currentIndex = newIndex;
    } else if (oldIndex < _currentIndex && newIndex >= _currentIndex) {
      _currentIndex--;
    } else if (oldIndex > _currentIndex && newIndex <= _currentIndex) {
      _currentIndex++;
    }

    _queueController.add(_queue);
    _currentIndexController.add(_currentIndex);
  }

  Future<void> setVolume(double volume) async {
    await _player.setVolume(volume.clamp(0.0, 1.0));
  }

  Future<void> setSpeed(double speed) async {
    await _player.setSpeed(speed.clamp(0.5, 2.0));
  }

  void dispose() {
    _player.dispose();
    _currentSongController.close();
    _queueController.close();
    _currentIndexController.close();
    _repeatModeController.close();
    _shuffleModeController.close();
  }
}
