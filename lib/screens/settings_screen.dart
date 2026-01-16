import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:file_picker/file_picker.dart';
import '../providers/providers.dart';
import '../services/services.dart';
import '../theme/app_theme.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final _permissionService = PermissionService();
  bool _hasPermission = false;

  @override
  void initState() {
    super.initState();
    _checkPermission();
  }

  Future<void> _checkPermission() async {
    final hasPermission = await _permissionService.checkStoragePermission();
    setState(() => _hasPermission = hasPermission);
  }

  Future<void> _requestPermission() async {
    final granted = await _permissionService.requestStoragePermission();
    setState(() => _hasPermission = granted);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.darkGrey,
      appBar: AppBar(
        backgroundColor: AppTheme.darkGrey,
        title: const Text('Settings', style: AppTheme.titleLarge),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: Consumer<LibraryProvider>(
        builder: (context, library, child) {
          return ListView(
            children: [
              // Permission section
              if (!_hasPermission) _buildPermissionCard(),

              // Music folders section
              _buildSectionHeader('Music Folders'),
              _buildAddFolderTile(),

              // Folder list
              if (library.folders.isEmpty)
                _buildEmptyFoldersMessage()
              else
                ...library.folders.map((folder) => _buildFolderTile(folder)),

              // Scan section
              if (library.folders.isNotEmpty) ...[
                const SizedBox(height: 16),
                _buildScanAllButton(library),
              ],

              // Library stats
              _buildSectionHeader('Library'),
              _buildStatsTile(library),

              // Playback section
              _buildSectionHeader('Playback'),
              _buildSwitchTile(
                'Gapless playback',
                'Seamless transition between tracks',
                true,
                (value) {},
              ),
              _buildSwitchTile(
                'Crossfade',
                'Fade between tracks',
                false,
                (value) {},
              ),

              // About section
              _buildSectionHeader('About'),
              _buildAboutTile(),

              const SizedBox(height: 100),
            ],
          );
        },
      ),
    );
  }

  Widget _buildPermissionCard() {
    return Container(
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.cardGrey,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppTheme.primaryGreen.withOpacity(0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                Icons.folder_outlined,
                color: AppTheme.primaryGreen,
              ),
              const SizedBox(width: 12),
              const Text(
                'Storage Permission Required',
                style: AppTheme.titleMedium,
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            'Optico needs access to your storage to scan and play music files.',
            style: AppTheme.bodyMedium.copyWith(color: AppTheme.textGrey),
          ),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: _requestPermission,
            child: const Text('Grant Permission'),
          ),
        ],
      ),
    );
  }

  Widget _buildSectionHeader(String title) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 24, 16, 8),
      child: Text(
        title,
        style: AppTheme.titleSmall.copyWith(color: AppTheme.textGrey),
      ),
    );
  }

  Widget _buildAddFolderTile() {
    return ListTile(
      leading: Container(
        width: 48,
        height: 48,
        decoration: BoxDecoration(
          color: AppTheme.lightGrey,
          borderRadius: BorderRadius.circular(8),
        ),
        child: const Icon(
          Icons.add,
          color: AppTheme.primaryGreen,
        ),
      ),
      title: const Text('Add Music Folder', style: AppTheme.titleSmall),
      subtitle: Text(
        'Select a folder containing music files',
        style: AppTheme.bodySmall,
      ),
      onTap: _addFolder,
    );
  }

  Future<void> _addFolder() async {
    if (!_hasPermission) {
      await _requestPermission();
      if (!_hasPermission) return;
    }

    try {
      final result = await FilePicker.platform.getDirectoryPath();
      if (result != null) {
        await context.read<LibraryProvider>().addFolder(result);
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Scanning folder: ${result.split('/').last}'),
              backgroundColor: AppTheme.cardGrey,
            ),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error adding folder: $e'),
            backgroundColor: AppTheme.errorRed,
          ),
        );
      }
    }
  }

  Widget _buildEmptyFoldersMessage() {
    return Container(
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: AppTheme.cardGrey,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        children: [
          Icon(
            Icons.folder_open_outlined,
            size: 48,
            color: AppTheme.textGrey,
          ),
          const SizedBox(height: 16),
          Text(
            'No music folders added',
            style: AppTheme.titleSmall,
          ),
          const SizedBox(height: 8),
          Text(
            'Add folders containing your music files to start listening',
            style: AppTheme.bodySmall,
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  Widget _buildFolderTile(folder) {
    final library = context.read<LibraryProvider>();

    return ListTile(
      leading: Container(
        width: 48,
        height: 48,
        decoration: BoxDecoration(
          color: AppTheme.lightGrey,
          borderRadius: BorderRadius.circular(8),
        ),
        child: const Icon(
          Icons.folder,
          color: AppTheme.textGrey,
        ),
      ),
      title: Text(folder.name, style: AppTheme.titleSmall),
      subtitle: Text(
        '${folder.songCount} songs • ${folder.path}',
        style: AppTheme.bodySmall,
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
      ),
      trailing: PopupMenuButton(
        icon: const Icon(Icons.more_vert, color: AppTheme.textGrey),
        color: AppTheme.mediumGrey,
        itemBuilder: (context) => [
          PopupMenuItem(
            value: 'rescan',
            child: Row(
              children: const [
                Icon(Icons.refresh, size: 20),
                SizedBox(width: 12),
                Text('Rescan'),
              ],
            ),
          ),
          PopupMenuItem(
            value: 'remove',
            child: Row(
              children: const [
                Icon(Icons.delete_outline, size: 20),
                SizedBox(width: 12),
                Text('Remove'),
              ],
            ),
          ),
        ],
        onSelected: (value) async {
          switch (value) {
            case 'rescan':
              await library.scanFolder(folder);
              break;
            case 'remove':
              await _confirmRemoveFolder(folder);
              break;
          }
        },
      ),
    );
  }

  Future<void> _confirmRemoveFolder(folder) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: AppTheme.mediumGrey,
        title: const Text('Remove Folder', style: AppTheme.titleLarge),
        content: Text(
          'Remove "${folder.name}" from your music library? The files will not be deleted.',
          style: AppTheme.bodyMedium,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.errorRed,
            ),
            child: const Text('Remove'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      await context.read<LibraryProvider>().removeFolder(folder.id);
    }
  }

  Widget _buildScanAllButton(LibraryProvider library) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: library.isScanning
          ? Column(
              children: [
                LinearProgressIndicator(
                  value: library.scanProgress,
                  backgroundColor: AppTheme.lightGrey,
                  valueColor:
                      const AlwaysStoppedAnimation<Color>(AppTheme.primaryGreen),
                ),
                const SizedBox(height: 8),
                Text(
                  library.scanningStatus,
                  style: AppTheme.bodySmall,
                ),
              ],
            )
          : OutlinedButton.icon(
              onPressed: () => library.scanAllFolders(),
              icon: const Icon(Icons.refresh),
              label: const Text('Rescan All Folders'),
            ),
    );
  }

  Widget _buildStatsTile(LibraryProvider library) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.cardGrey,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        children: [
          _buildStatRow('Songs', library.stats['songs']?.toString() ?? '0'),
          const SizedBox(height: 12),
          _buildStatRow('Albums', library.stats['albums']?.toString() ?? '0'),
          const SizedBox(height: 12),
          _buildStatRow('Artists', library.stats['artists']?.toString() ?? '0'),
          const SizedBox(height: 12),
          _buildStatRow('Playlists', library.stats['playlists']?.toString() ?? '0'),
        ],
      ),
    );
  }

  Widget _buildStatRow(String label, String value) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label, style: AppTheme.bodyMedium),
        Text(value, style: AppTheme.titleSmall),
      ],
    );
  }

  Widget _buildSwitchTile(
    String title,
    String subtitle,
    bool value,
    ValueChanged<bool> onChanged,
  ) {
    return SwitchListTile(
      title: Text(title, style: AppTheme.titleSmall),
      subtitle: Text(subtitle, style: AppTheme.bodySmall),
      value: value,
      onChanged: onChanged,
      activeColor: AppTheme.primaryGreen,
    );
  }

  Widget _buildAboutTile() {
    return ListTile(
      leading: Container(
        width: 48,
        height: 48,
        decoration: BoxDecoration(
          color: AppTheme.primaryGreen,
          borderRadius: BorderRadius.circular(8),
        ),
        child: const Icon(
          Icons.music_note,
          color: AppTheme.black,
        ),
      ),
      title: const Text('Optico', style: AppTheme.titleSmall),
      subtitle: Text(
        'Version 1.0.0',
        style: AppTheme.bodySmall,
      ),
      onTap: () {
        showAboutDialog(
          context: context,
          applicationName: 'Optico',
          applicationVersion: '1.0.0',
          applicationIcon: Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              color: AppTheme.primaryGreen,
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Icon(
              Icons.music_note,
              color: AppTheme.black,
            ),
          ),
          children: [
            const Text(
              'A modern local music player with Spotify-like design.',
            ),
          ],
        );
      },
    );
  }
}
