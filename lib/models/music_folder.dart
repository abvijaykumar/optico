class MusicFolder {
  final String id;
  final String path;
  final String name;
  final int songCount;
  final DateTime? lastScanned;
  final bool isEnabled;

  MusicFolder({
    required this.id,
    required this.path,
    required this.name,
    this.songCount = 0,
    this.lastScanned,
    this.isEnabled = true,
  });

  MusicFolder copyWith({
    String? id,
    String? path,
    String? name,
    int? songCount,
    DateTime? lastScanned,
    bool? isEnabled,
  }) {
    return MusicFolder(
      id: id ?? this.id,
      path: path ?? this.path,
      name: name ?? this.name,
      songCount: songCount ?? this.songCount,
      lastScanned: lastScanned ?? this.lastScanned,
      isEnabled: isEnabled ?? this.isEnabled,
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'path': path,
      'name': name,
      'songCount': songCount,
      'lastScanned': lastScanned?.millisecondsSinceEpoch,
      'isEnabled': isEnabled ? 1 : 0,
    };
  }

  factory MusicFolder.fromMap(Map<String, dynamic> map) {
    return MusicFolder(
      id: map['id'] as String,
      path: map['path'] as String,
      name: map['name'] as String,
      songCount: map['songCount'] as int? ?? 0,
      lastScanned: map['lastScanned'] != null
          ? DateTime.fromMillisecondsSinceEpoch(map['lastScanned'] as int)
          : null,
      isEnabled: map['isEnabled'] == 1,
    );
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is MusicFolder && other.id == id;
  }

  @override
  int get hashCode => id.hashCode;

  @override
  String toString() {
    return 'MusicFolder(id: $id, path: $path, name: $name, songCount: $songCount)';
  }
}
