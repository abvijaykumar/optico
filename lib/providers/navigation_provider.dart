import 'package:flutter/foundation.dart';

class NavigationProvider extends ChangeNotifier {
  int _currentIndex = 0;
  bool _isPlayerExpanded = false;

  int get currentIndex => _currentIndex;
  bool get isPlayerExpanded => _isPlayerExpanded;

  void setIndex(int index) {
    _currentIndex = index;
    notifyListeners();
  }

  void expandPlayer() {
    _isPlayerExpanded = true;
    notifyListeners();
  }

  void collapsePlayer() {
    _isPlayerExpanded = false;
    notifyListeners();
  }

  void togglePlayerExpanded() {
    _isPlayerExpanded = !_isPlayerExpanded;
    notifyListeners();
  }
}
