import 'package:flutter/material.dart';
import '../models/models.dart';
import '../theme/app_theme.dart';

class ArtistCard extends StatelessWidget {
  final Artist artist;
  final VoidCallback? onTap;
  final double size;

  const ArtistCard({
    super.key,
    required this.artist,
    this.onTap,
    this.size = 150,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: size,
        child: Column(
          children: [
            _buildArtistAvatar(),
            const SizedBox(height: 12),
            Text(
              artist.displayName,
              style: AppTheme.titleSmall,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 4),
            Text(
              'Artist',
              style: AppTheme.bodySmall,
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildArtistAvatar() {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: AppTheme.lightGrey,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.3),
            blurRadius: 20,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      child: ClipOval(
        child: artist.artistImage != null && artist.artistImage!.isNotEmpty
            ? Image.memory(
                artist.artistImage!,
                fit: BoxFit.cover,
                width: size,
                height: size,
              )
            : Icon(
                Icons.person_rounded,
                color: AppTheme.textGrey,
                size: size * 0.5,
              ),
      ),
    );
  }
}

class ArtistListTile extends StatelessWidget {
  final Artist artist;
  final VoidCallback? onTap;
  final VoidCallback? onMoreTap;

  const ArtistListTile({
    super.key,
    required this.artist,
    this.onTap,
    this.onMoreTap,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: Row(
            children: [
              _buildAvatar(),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      artist.displayName,
                      style: AppTheme.titleSmall,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${artist.albumCount} albums • ${artist.songCount} songs',
                      style: AppTheme.bodySmall,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
              if (onMoreTap != null)
                IconButton(
                  icon: const Icon(Icons.more_vert, size: 20),
                  color: AppTheme.textGrey,
                  onPressed: onMoreTap,
                ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildAvatar() {
    return Container(
      width: 56,
      height: 56,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: AppTheme.lightGrey,
      ),
      child: ClipOval(
        child: artist.artistImage != null && artist.artistImage!.isNotEmpty
            ? Image.memory(
                artist.artistImage!,
                fit: BoxFit.cover,
              )
            : const Icon(
                Icons.person_rounded,
                color: AppTheme.textGrey,
                size: 28,
              ),
      ),
    );
  }
}
