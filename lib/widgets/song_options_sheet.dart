import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/models.dart';
import '../providers/providers.dart';
import '../theme/app_theme.dart';
import 'album_art.dart';

class SongOptionsSheet extends StatelessWidget {
  final Song song;

  const SongOptionsSheet({
    super.key,
    required this.song,
  });

  static Future<void> show(BuildContext context, Song song) async {
    await showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (context) => SongOptionsSheet(song: song),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: AppTheme.mediumGrey,
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Handle
          Container(
            width: 40,
            height: 4,
            margin: const EdgeInsets.only(top: 12),
            decoration: BoxDecoration(
              color: AppTheme.textGrey,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          // Song info
          Padding(
            padding: const EdgeInsets.all(20),
            child: Row(
              children: [
                AlbumArt(
                  albumArt: song.albumArt,
                  size: 56,
                  borderRadius: 4,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        song.displayTitle,
                        style: AppTheme.titleMedium,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      const SizedBox(height: 4),
                      Text(
                        song.displayArtist,
                        style: AppTheme.bodySmall,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const Divider(height: 1, color: AppTheme.lightGrey),
          // Options
          _buildOption(
            context,
            icon: song.isFavorite ? Icons.favorite : Icons.favorite_border,
            iconColor: song.isFavorite ? AppTheme.primaryGreen : AppTheme.white,
            title: song.isFavorite ? 'Remove from Liked Songs' : 'Add to Liked Songs',
            onTap: () {
              context.read<LibraryProvider>().toggleFavorite(song);
              Navigator.pop(context);
            },
          ),
          _buildOption(
            context,
            icon: Icons.playlist_add,
            title: 'Add to playlist',
            onTap: () {
              Navigator.pop(context);
              _showAddToPlaylistDialog(context, song);
            },
          ),
          _buildOption(
            context,
            icon: Icons.queue_music,
            title: 'Add to queue',
            onTap: () {
              context.read<PlayerProvider>().addToQueue(song);
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Added to queue')),
              );
            },
          ),
          _buildOption(
            context,
            icon: Icons.skip_next,
            title: 'Play next',
            onTap: () {
              context.read<PlayerProvider>().addToQueueNext(song);
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Will play next')),
              );
            },
          ),
          _buildOption(
            context,
            icon: Icons.album,
            title: 'Go to album',
            onTap: () {
              Navigator.pop(context);
              // TODO: Navigate to album
            },
          ),
          _buildOption(
            context,
            icon: Icons.person,
            title: 'Go to artist',
            onTap: () {
              Navigator.pop(context);
              // TODO: Navigate to artist
            },
          ),
          const SizedBox(height: 16),
        ],
      ),
    );
  }

  Widget _buildOption(
    BuildContext context, {
    required IconData icon,
    required String title,
    Color? iconColor,
    required VoidCallback onTap,
  }) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
          child: Row(
            children: [
              Icon(
                icon,
                color: iconColor ?? AppTheme.white,
                size: 24,
              ),
              const SizedBox(width: 16),
              Text(
                title,
                style: AppTheme.bodyLarge,
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _showAddToPlaylistDialog(BuildContext context, Song song) {
    final playlists = context.read<LibraryProvider>().playlists;

    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (context) => Container(
        decoration: const BoxDecoration(
          color: AppTheme.mediumGrey,
          borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 40,
              height: 4,
              margin: const EdgeInsets.only(top: 12),
              decoration: BoxDecoration(
                color: AppTheme.textGrey,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(20),
              child: Text(
                'Add to playlist',
                style: AppTheme.titleLarge,
              ),
            ),
            // Create new playlist option
            _buildPlaylistOption(
              context,
              icon: Icons.add,
              title: 'Create new playlist',
              onTap: () async {
                Navigator.pop(context);
                final name = await _showCreatePlaylistDialog(context);
                if (name != null && name.isNotEmpty) {
                  final library = context.read<LibraryProvider>();
                  final playlist = await library.createPlaylist(name);
                  await library.addSongToPlaylist(playlist.id, song.id);
                }
              },
            ),
            const Divider(height: 1, color: AppTheme.lightGrey),
            // Existing playlists
            if (playlists.isNotEmpty)
              ConstrainedBox(
                constraints: BoxConstraints(
                  maxHeight: MediaQuery.of(context).size.height * 0.4,
                ),
                child: ListView.builder(
                  shrinkWrap: true,
                  itemCount: playlists.length,
                  itemBuilder: (context, index) {
                    final playlist = playlists[index];
                    return _buildPlaylistOption(
                      context,
                      icon: Icons.queue_music,
                      title: playlist.name,
                      subtitle: '${playlist.songCount} songs',
                      onTap: () async {
                        await context
                            .read<LibraryProvider>()
                            .addSongToPlaylist(playlist.id, song.id);
                        Navigator.pop(context);
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(
                            content: Text('Added to ${playlist.name}'),
                          ),
                        );
                      },
                    );
                  },
                ),
              ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }

  Widget _buildPlaylistOption(
    BuildContext context, {
    required IconData icon,
    required String title,
    String? subtitle,
    required VoidCallback onTap,
  }) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
          child: Row(
            children: [
              Icon(icon, color: AppTheme.white, size: 24),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(title, style: AppTheme.bodyLarge),
                    if (subtitle != null)
                      Text(subtitle, style: AppTheme.bodySmall),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<String?> _showCreatePlaylistDialog(BuildContext context) async {
    final controller = TextEditingController();
    return showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: AppTheme.mediumGrey,
        title: const Text(
          'Create playlist',
          style: AppTheme.titleLarge,
        ),
        content: TextField(
          controller: controller,
          autofocus: true,
          style: AppTheme.bodyLarge,
          decoration: const InputDecoration(
            hintText: 'Playlist name',
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, controller.text),
            child: const Text('Create'),
          ),
        ],
      ),
    );
  }
}
