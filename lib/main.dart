import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'providers/providers.dart';
import 'services/services.dart';
import 'screens/screens.dart';
import 'theme/app_theme.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Set system UI overlay style
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.light,
      systemNavigationBarColor: AppTheme.black,
      systemNavigationBarIconBrightness: Brightness.light,
    ),
  );

  // Set preferred orientations
  await SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
    DeviceOrientation.portraitDown,
  ]);

  runApp(const OpticoApp());
}

class OpticoApp extends StatelessWidget {
  const OpticoApp({super.key});

  @override
  Widget build(BuildContext context) {
    // Initialize services
    final databaseService = DatabaseService();
    final scannerService = MusicScannerService();
    final audioService = AudioPlayerService();

    return MultiProvider(
      providers: [
        // Services
        Provider<DatabaseService>.value(value: databaseService),
        Provider<MusicScannerService>.value(value: scannerService),
        Provider<AudioPlayerService>.value(value: audioService),

        // Providers
        ChangeNotifierProvider<LibraryProvider>(
          create: (_) => LibraryProvider(
            databaseService: databaseService,
            scannerService: scannerService,
          )..initialize(),
        ),
        ChangeNotifierProvider<PlayerProvider>(
          create: (_) => PlayerProvider(
            audioService: audioService,
            databaseService: databaseService,
          ),
        ),
        ChangeNotifierProvider<NavigationProvider>(
          create: (_) => NavigationProvider(),
        ),
      ],
      child: MaterialApp(
        title: 'Optico',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.darkTheme,
        home: const MainNavigation(),
        routes: {
          '/settings': (context) => const SettingsScreen(),
          '/player': (context) => const PlayerScreen(),
        },
      ),
    );
  }
}
