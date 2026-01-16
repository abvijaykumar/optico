import 'package:flutter/foundation.dart';
import 'package:just_audio/just_audio.dart';
import '../models/models.dart';
import '../services/services.dart';

class PlayerProvider extends ChangeNotifier {
  final AudioPlayerService _audioService;
  final DatabaseService _databaseService;

  Song? _currentSong;
  List<Song> _queue = [];
  int _currentIndex = -1;
  bool _isPlaying = false;
  Duration _position = Duration.zero;
  Duration _duration = Duration.zero;
  RepeatMode _repeatMode = RepeatMode.off;
  ShuffleMode _shuffleMode = ShuffleMode.off;
  bool _isMiniPlayerVisible = false;

  // Getters
  Song? get currentSong => _currentSong;
  List<Song> get queue => _queue;
  int get currentIndex => _currentIndex;
  bool get isPlaying => _isPlaying;
  Duration get position => _position;
  Duration get duration => _duration;
  RepeatMode get repeatMode => _repeatMode;
  ShuffleMode get shuffleMode => _shuffleMode;
  bool get isMiniPlayerVisible => _isMiniPlayerVisible;
  bool get hasNext => _audioService.hasNext;
  bool get hasPrevious => _audioService.hasPrevious;
  AudioPlayerService get audioService => _audioService;

  double get progress {
    if (_duration.inMilliseconds == 0) return 0;
    return _position.inMilliseconds / _duration.inMilliseconds;
  }

  PlayerProvider({
    required AudioPlayerService audioService,
    required DatabaseService databaseService,
  })  : _audioService = audioService,
        _databaseService = databaseService {
    _initializeListeners();
  }

  void _initializeListeners() {
    _audioService.currentSongStream.listen((song) {
      _currentSong = song;
      _isMiniPlayerVisible = song != null;
      notifyListeners();
    });

    _audioService.queueStream.listen((queue) {
      _queue = queue;
      notifyListeners();
    });

    _audioService.currentIndexStream.listen((index) {
      _currentIndex = index;
      notifyListeners();
    });

    _audioService.playingStream.listen((playing) {
      _isPlaying = playing;
      notifyListeners();
    });

    _audioService.positionStream.listen((position) {
      _position = position;
      notifyListeners();
    });

    _audioService.durationStream.listen((duration) {
      _duration = duration ?? Duration.zero;
      notifyListeners();
    });

    _audioService.repeatModeStream.listen((mode) {
      _repeatMode = mode;
      notifyListeners();
    });

    _audioService.shuffleModeStream.listen((mode) {
      _shuffleMode = mode;
      notifyListeners();
    });
  }

  Future<void> playSong(Song song) async {
    await _audioService.playSong(song);
    await _recordPlay(song);
  }

  Future<void> playQueue(List<Song> songs, {int startIndex = 0}) async {
    await _audioService.playQueue(songs, startIndex: startIndex);
    if (songs.isNotEmpty && startIndex < songs.length) {
      await _recordPlay(songs[startIndex]);
    }
  }

  Future<void> play() async {
    await _audioService.play();
  }

  Future<void> pause() async {
    await _audioService.pause();
  }

  Future<void> togglePlayPause() async {
    await _audioService.togglePlayPause();
  }

  Future<void> stop() async {
    await _audioService.stop();
  }

  Future<void> seek(Duration position) async {
    await _audioService.seek(position);
  }

  Future<void> seekToPercent(double percent) async {
    final position = Duration(
      milliseconds: (_duration.inMilliseconds * percent).round(),
    );
    await seek(position);
  }

  Future<void> next() async {
    await _audioService.next();
    if (_currentSong != null) {
      await _recordPlay(_currentSong!);
    }
  }

  Future<void> previous() async {
    await _audioService.previous();
    if (_currentSong != null) {
      await _recordPlay(_currentSong!);
    }
  }

  Future<void> skipToIndex(int index) async {
    await _audioService.skipToIndex(index);
    if (_currentSong != null) {
      await _recordPlay(_currentSong!);
    }
  }

  void toggleRepeatMode() {
    _audioService.toggleRepeatMode();
  }

  void toggleShuffleMode() {
    _audioService.toggleShuffleMode();
  }

  void addToQueue(Song song) {
    _audioService.addToQueue(song);
  }

  void addToQueueNext(Song song) {
    _audioService.addToQueueNext(song);
  }

  void removeFromQueue(int index) {
    _audioService.removeFromQueue(index);
  }

  void clearQueue() {
    _audioService.clearQueue();
  }

  void reorderQueue(int oldIndex, int newIndex) {
    _audioService.reorderQueue(oldIndex, newIndex);
  }

  Future<void> setVolume(double volume) async {
    await _audioService.setVolume(volume);
  }

  Future<void> setSpeed(double speed) async {
    await _audioService.setSpeed(speed);
  }

  Future<void> _recordPlay(Song song) async {
    await _databaseService.incrementPlayCount(song.id);
    await _databaseService.addRecentPlay(song.id);
  }

  void hideMiniPlayer() {
    _isMiniPlayerVisible = false;
    notifyListeners();
  }

  void showMiniPlayer() {
    if (_currentSong != null) {
      _isMiniPlayerVisible = true;
      notifyListeners();
    }
  }

  @override
  void dispose() {
    _audioService.dispose();
    super.dispose();
  }
}
