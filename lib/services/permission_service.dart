import 'dart:io';
import 'package:permission_handler/permission_handler.dart';

class PermissionService {
  Future<bool> requestStoragePermission() async {
    if (Platform.isAndroid) {
      // For Android 13+ (API 33+), use specific media permissions
      final androidInfo = await _getAndroidVersion();
      if (androidInfo >= 33) {
        final audioStatus = await Permission.audio.request();
        return audioStatus.isGranted;
      } else if (androidInfo >= 30) {
        // Android 11-12: Use manage external storage
        final status = await Permission.manageExternalStorage.request();
        if (status.isGranted) return true;

        // Fallback to regular storage
        final storageStatus = await Permission.storage.request();
        return storageStatus.isGranted;
      } else {
        // Android 10 and below
        final status = await Permission.storage.request();
        return status.isGranted;
      }
    } else if (Platform.isIOS) {
      // iOS doesn't need storage permission for accessing music library
      // through the file picker
      return true;
    }
    return false;
  }

  Future<bool> checkStoragePermission() async {
    if (Platform.isAndroid) {
      final androidInfo = await _getAndroidVersion();
      if (androidInfo >= 33) {
        return await Permission.audio.isGranted;
      } else if (androidInfo >= 30) {
        return await Permission.manageExternalStorage.isGranted ||
            await Permission.storage.isGranted;
      } else {
        return await Permission.storage.isGranted;
      }
    } else if (Platform.isIOS) {
      return true;
    }
    return false;
  }

  Future<bool> requestNotificationPermission() async {
    if (Platform.isAndroid) {
      final status = await Permission.notification.request();
      return status.isGranted;
    }
    return true;
  }

  Future<void> openAppSettings() async {
    await openAppSettings();
  }

  Future<int> _getAndroidVersion() async {
    if (!Platform.isAndroid) return 0;

    try {
      // This is a simplified version - in production, use device_info_plus
      final result = await Process.run('getprop', ['ro.build.version.sdk']);
      return int.tryParse(result.stdout.toString().trim()) ?? 0;
    } catch (e) {
      return 30; // Default to Android 11 behavior
    }
  }

  Future<PermissionStatus> getStoragePermissionStatus() async {
    if (Platform.isAndroid) {
      final androidInfo = await _getAndroidVersion();
      if (androidInfo >= 33) {
        return await Permission.audio.status;
      } else if (androidInfo >= 30) {
        final manageStatus = await Permission.manageExternalStorage.status;
        if (manageStatus.isGranted) return manageStatus;
        return await Permission.storage.status;
      } else {
        return await Permission.storage.status;
      }
    }
    return PermissionStatus.granted;
  }
}
