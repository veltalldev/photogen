

class BackendSettingsInterface extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final settings = ref.watch(settingsProvider);
    final isEditing = ref.watch(isEditingSettingsProvider);
    
    return Card(
      margin: EdgeInsets.all(16),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.settings, color: Colors.grey.shade700),
                SizedBox(width: 8),
                Text(
                  'Backend Settings',
                  style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                Spacer(),
                TextButton(
                  onPressed: () => ref.read(isEditingSettingsProvider.notifier).state = !isEditing,
                  child: Text(isEditing ? 'Cancel' : 'Edit'),
                ),
              ],
            ),
            
            Divider(),
            
            // Connection settings
            _buildConnectionSettings(context, ref, settings, isEditing),
            
            Divider(),
            
            // Generation defaults
            _buildGenerationDefaults(context, ref, settings, isEditing),
            
            Divider(),
            
            // Remote backend settings
            if (settings.useRemoteBackend || isEditing)
              _buildRemoteSettings(context, ref, settings, isEditing),
            
            if (isEditing) ...[
              Divider(),
              
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  ElevatedButton(
                    onPressed: () => _saveSettings(context, ref),
                    child: Text('Save Changes'),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }
  
  Widget _buildConnectionSettings(
    BuildContext context, 
    WidgetRef ref, 
    AppSettings settings, 
    bool isEditing
  ) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Connection',
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
        SizedBox(height: 16),
        
        // Backend mode
        ListTile(
          contentPadding: EdgeInsets.zero,
          title: Text('Backend Mode'),
          subtitle: Text(settings.useRemoteBackend ? 'Remote' : 'Local'),
          trailing: isEditing
              ? Switch(
                  value: settings.useRemoteBackend,
                  onChanged: (value) => ref.read(settingsProvider.notifier).updateUseRemote(value),
                )
              : null,
        ),
        
        // Local URL
        if (!settings.useRemoteBackend || isEditing)
          isEditing
              ? TextFormField(
                  decoration: InputDecoration(
                    labelText: 'Local InvokeAI URL',
                    hintText: 'http://localhost:9090',
                  ),
                  initialValue: settings.localBackendUrl,
                  onChanged: (value) => ref.read(settingsProvider.notifier).updateLocalUrl(value),
                )
              : ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: Text('Local InvokeAI URL'),
                  subtitle: Text(settings.localBackendUrl),
                ),
        
        SizedBox(height: 8),
        
        // Connection test button
        OutlinedButton.icon(
          icon: Icon(Icons.link),
          label: Text('Test Connection'),
          onPressed: () => _testConnection(context, ref),
        ),
      ],
    );
  }
  
  Widget _buildGenerationDefaults(
    BuildContext context, 
    WidgetRef ref, 
    AppSettings settings, 
    bool isEditing
  ) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Generation Defaults',
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
        SizedBox(height: 16),
        
        // Default dimensions
        if (isEditing) ...[
          Row(
            children: [
              Expanded(
                child: TextFormField(
                  decoration: InputDecoration(
                    labelText: 'Default Width',
                  ),
                  initialValue: settings.defaultWidth.toString(),
                  keyboardType: TextInputType.number,
                  onChanged: (value) => ref.read(settingsProvider.notifier)
                      .updateDefaultWidth(int.tryParse(value) ?? 1024),
                ),
              ),
              SizedBox(width: 16),
              Expanded(
                child: TextFormField(
                  decoration: InputDecoration(
                    labelText: 'Default Height',
                  ),
                  initialValue: settings.defaultHeight.toString(),
                  keyboardType: TextInputType.number,
                  onChanged: (value) => ref.read(settingsProvider.notifier)
                      .updateDefaultHeight(int.tryParse(value) ?? 1024),
                ),
              ),
            ],
          ),
          SizedBox(height: 16),
          
          // Default steps
          TextFormField(
            decoration: InputDecoration(
              labelText: 'Default Steps',
            ),
            initialValue: settings.defaultSteps.toString(),
            keyboardType: TextInputType.number,
            onChanged: (value) => ref.read(settingsProvider.notifier)
                .updateDefaultSteps(int.tryParse(value) ?? 30),
          ),
          SizedBox(height: 16),
          
          // Default CFG Scale
          TextFormField(
            decoration: InputDecoration(
              labelText: 'Default CFG Scale',
            ),
            initialValue: settings.defaultCfgScale.toString(),
            keyboardType: TextInputType.numberWithOptions(decimal: true),
            onChanged: (value) => ref.read(settingsProvider.notifier)
                .updateDefaultCfgScale(double.tryParse(value) ?? 7.5),
          ),
          SizedBox(height: 16),
          
          // Default scheduler
          DropdownButtonFormField<String>(
            decoration: InputDecoration(
              labelText: 'Default Scheduler',
            ),
            value: settings.defaultScheduler,
            items: [
              'euler',
              'euler_ancestral',
              'dpm_2',
              'dpm_2_ancestral',
              'dpmpp_2m',
            ].map((scheduler) => DropdownMenuItem(
              value: scheduler,
              child: Text(scheduler),
            )).toList(),
            onChanged: (value) {
              if (value != null) {
                ref.read(settingsProvider.notifier).updateDefaultScheduler(value);
              }
            },
          ),
          SizedBox(height: 16),
          
          // Default batch size
          TextFormField(
            decoration: InputDecoration(
              labelText: 'Default Batch Size',
            ),
            initialValue: settings.defaultBatchSize.toString(),
            keyboardType: TextInputType.number,
            onChanged: (value) => ref.read(settingsProvider.notifier)
                .updateDefaultBatchSize(int.tryParse(value) ?? 4),
          ),
        ] else ...[
          // Read-only view
          _buildSettingRow('Default Dimensions', '${settings.defaultWidth}×${settings.defaultHeight}'),
          _buildSettingRow('Default Steps', settings.defaultSteps.toString()),
          _buildSettingRow('Default CFG Scale', settings.defaultCfgScale.toString()),
          _buildSettingRow('Default Scheduler', settings.defaultScheduler),
          _buildSettingRow('Default Batch Size', settings.defaultBatchSize.toString()),
        ],
      ],
    );
  }
  
  Widget _buildRemoteSettings(
    BuildContext context, 
    WidgetRef ref, 
    AppSettings settings, 
    bool isEditing
  ) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Remote Backend Settings',
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
        SizedBox(height: 16),
        
        if (isEditing) ...[
          // RunPod API Key
          TextFormField(
            decoration: InputDecoration(
              labelText: 'RunPod API Key',
              hintText: 'Enter your RunPod API key',
            ),
            initialValue: settings.runpodApiKey,
            obscureText: true,
            onChanged: (value) => ref.read(settingsProvider.notifier).updateRunpodApiKey(value),
          ),
          SizedBox(height: 16),
          
          // Remote backend URL
          TextFormField(
            decoration: InputDecoration(
              labelText: 'Remote Backend URL',
              hintText: 'https://{pod-id}-9090.proxy.runpod.net',
            ),
            initialValue: settings.remoteBackendUrl,
            onChanged: (value) => ref.read(settingsProvider.notifier).updateRemoteUrl(value),
          ),
          SizedBox(height: 16),
          
          // Pod Type
          DropdownButtonFormField<String>(
            decoration: InputDecoration(
              labelText: 'RunPod Type',
            ),
            value: settings.runpodPodType,
            items: [
              'NVIDIA A5000',
              'NVIDIA RTX A4000',
              'NVIDIA RTX 3090',
              'NVIDIA RTX A6000',
            ].map((type) => DropdownMenuItem(
              value: type,
              child: Text(type),
            )).toList(),
            onChanged: (value) {
              if (value != null) {
                ref.read(settingsProvider.notifier).updateRunpodPodType(value);
              }
            },
          ),
          SizedBox(height: 16),
          
          // Idle timeout
          TextFormField(
            decoration: InputDecoration(
              labelText: 'Idle Timeout (minutes)',
              hintText: 'Time before auto-shutdown',
            ),
            initialValue: settings.idleTimeoutMinutes.toString(),
            keyboardType: TextInputType.number,
            onChanged: (value) => ref.read(settingsProvider.notifier)
                .updateIdleTimeout(int.tryParse(value) ?? 30),
          ),
        ] else ...[
          // Read-only view
          if (settings.runpodApiKey != null && settings.runpodApiKey!.isNotEmpty)
            _buildSettingRow('RunPod API Key', '●●●●●●●●●●●●'),
          else
            _buildSettingRow('RunPod API Key', 'Not set'),
            
          _buildSettingRow('Remote Backend URL', settings.remoteBackendUrl ?? 'Not set'),
          _buildSettingRow('RunPod Type', settings.runpodPodType),
          _buildSettingRow('Idle Timeout', '${settings.idleTimeoutMinutes} minutes'),
        ],
        
        SizedBox(height: 16),
        
        // Pod management buttons
        if (settings.useRemoteBackend) ...[
          Row(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              // View cost history
              OutlinedButton.icon(
                icon: Icon(Icons.history),
                label: Text('Cost History'),
                onPressed: () => _showCostHistory(context, ref),
              ),
              
              SizedBox(width: 8),
              
              // Start/stop pod
              Consumer(
                builder: (context, ref, _) {
                  final backendStatus = ref.watch(backendStatusProvider);
                  return ElevatedButton.icon(
                    icon: Icon(backendStatus.isConnected ? Icons.stop : Icons.play_arrow),
                    label: Text(backendStatus.isConnected ? 'Stop Pod' : 'Start Pod'),
                    style: ElevatedButton.styleFrom(
                      primary: backendStatus.isConnected ? Colors.red : Colors.green,
                    ),
                    onPressed: () {
                      if (backendStatus.isConnected) {
                        ref.read(backendManagerProvider).stopPod();
                      } else {
                        ref.read(backendManagerProvider).startPod();
                      }
                    },
                  );
                },
              ),
            ],
          ),
        ],
      ],
    );
  }
  
  Widget _buildSettingRow(String label, String value) {
    return Padding(
      padding: EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '$label:',
            style: TextStyle(
              fontWeight: FontWeight.w500,
              color: Colors.grey.shade700,
            ),
          ),
          SizedBox(width: 8),
          Expanded(
            child: Text(
              value,
              textAlign: TextAlign.right,
            ),
          ),
        ],
      ),
    );
  }
  
  void _testConnection(BuildContext context, WidgetRef ref) {
    final settings = ref.read(settingsProvider);
    final backendManager = ref.read(backendManagerProvider);
    
    // Show testing dialog
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        title: Text('Testing Connection'),
        content: Row(
          children: [
            CircularProgressIndicator(),
            SizedBox(width: 16),
            Text('Connecting to InvokeAI...'),
          ],
        ),
      ),
    );
    
    // Test connection
    backendManager.testConnection().then((status) {
      // Close dialog
      Navigator.of(context).pop();
      
      // Show result
      if (status.isConnected) {
        showDialog(
          context: context,
          builder: (context) => AlertDialog(
            title: Text('Connection Successful'),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Successfully connected to InvokeAI.'),
                SizedBox(height: 8),
                Text('URL: ${status.baseUrl}'),
                if (status.apiVersion != null)
                  Text('API Version: ${status.apiVersion}'),
                if (status.isRemote && status.podStatus != null)
                  Text('Pod Status: ${status.podStatus}'),
              ],
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(context).pop(),
                child: Text('Close'),
              ),
            ],
          ),
        );
      } else {
        showDialog(
          context: context,
          builder: (context) => AlertDialog(
            title: Text('Connection Failed'),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Failed to connect to InvokeAI.'),
                SizedBox(height: 8),
                Text('URL: ${status.baseUrl}'),
                if (status.error != null)
                  Text('Error: ${status.error}'),
              ],
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(context).pop(),
                child: Text('Close'),
              ),
            ],
          ),
        );
      }
    });
  }
  
  void _saveSettings(BuildContext context, WidgetRef ref) {
    // Validate settings
    final settings = ref.read(settingsProvider);
    
    // Validate URLs
    if (!_isValidUrl(settings.localBackendUrl)) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Invalid local backend URL')),
      );
      return;
    }
    
    if (settings.useRemoteBackend) {
      if (settings.remoteBackendUrl == null || !_isValidUrl(settings.remoteBackendUrl!)) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Invalid remote backend URL')),
        );
        return;
      }
      
      if (settings.runpodApiKey == null || settings.runpodApiKey!.isEmpty) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('RunPod API key is required for remote mode')),
        );
        return;
      }
    }
    
    // Save settings
    ref.read(settingsProvider.notifier).saveSettings().then((_) {
      // Exit editing mode
      ref.read(isEditingSettingsProvider.notifier).state = false;
      
      // Show success message
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Settings saved successfully')),
      );
      
      // Update backend connection
      ref.refresh(backendStatusProvider);
    }).catchError((error) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error saving settings: $error')),
      );
    });
  }
  
  bool _isValidUrl(String url) {
    try {
      final uri = Uri.parse(url);
      return uri.scheme == 'http' || uri.scheme == 'https';
    } catch (_) {
      return false;
    }
  }
  
  void _showCostHistory(BuildContext context, WidgetRef ref) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Cost History'),
        content: Container(
          width: double.maxFinite,
          child: Consumer(
            builder: (context, ref, _) {
              final costAsync = ref.watch(costHistoryProvider);
              
              return costAsync.when(
                data: (history) {
                  if (history.isEmpty) {
                    return Center(
                      child: Text('No cost history available'),
                    );
                  }
                  
                  // Calculate total cost
                  final totalCost = history.fold<double>(
                    0, (sum, record) => sum + record.cost
                  );
                  
                  return Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Total Cost: \${totalCost.toStringAsFixed(2)}',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          color: Colors.orange,
                        ),
                      ),
                      SizedBox(height: 16),
                      Expanded(
                        child: ListView.builder(
                          itemCount: history.length,
                          itemBuilder: (context, index) {
                            final record = history[index];
                            return ListTile(
                              title: Text('Session on ${_formatDate(record.sessionDate)}'),
                              subtitle: Text('Duration: ${_formatDuration(record.duration)}'),
                              trailing: Text(
                                '\${record.cost.toStringAsFixed(2)}',
                                style: TextStyle(
                                  fontWeight: FontWeight.bold,
                                  color: Colors.orange,
                                ),
                              ),
                            );
                          },
                        ),
                      ),
                    ],
                  );
                },
                loading: () => Center(child: CircularProgressIndicator()),
                error: (error, _) => Center(
                  child: Text('Error loading cost history: $error'),
                ),
              );
            },
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: Text('Close'),
          ),
        ],
      ),
    );
  }
  
  String _formatDate(DateTime date) {
    return '${date.month}/${date.day}/${date.year}';
  }
  
  String _formatDuration(Duration duration) {
    final hours = duration.inHours;
    final minutes = duration.inMinutes % 60;
    
    if (hours > 0) {
      return '$hours hr ${minutes} min';
    } else {
      return '${minutes} min';
    }
  }
}

// Provider for the editing state
final isEditingSettingsProvider = StateProvider<bool>((ref) => false);

// App settings model
class AppSettings {
  final bool useRemoteBackend;
  final String localBackendUrl;
  final String? remoteBackendUrl;
  final String? runpodApiKey;
  final String runpodPodType;
  final int idleTimeoutMinutes;
  final int defaultWidth;
  final int defaultHeight;
  final int defaultSteps;
  final double defaultCfgScale;
  final String defaultScheduler;
  final int defaultBatchSize;
  
  AppSettings({
    this.useRemoteBackend = false,
    this.localBackendUrl = 'http://localhost:9090',
    this.remoteBackendUrl,
    this.runpodApiKey,
    this.runpodPodType = 'NVIDIA A5000',
    this.idleTimeoutMinutes = 30,
    this.defaultWidth = 1024,
    this.defaultHeight = 1024,
    this.defaultSteps = 30,
    this.defaultCfgScale = 7.5,
    this.defaultScheduler = 'euler',
    this.defaultBatchSize = 4,
  });
  
  AppSettings copyWith({
    bool? useRemoteBackend,
    String? localBackendUrl,
    String? remoteBackendUrl,
    String? runpodApiKey,
    String? runpodPodType,
    int? idleTimeoutMinutes,
    int? defaultWidth,
    int? defaultHeight,
    int? defaultSteps,
    double? defaultCfgScale,
    String? defaultScheduler,
    int? defaultBatchSize,
  }) {
    return AppSettings(
      useRemoteBackend: useRemoteBackend ?? this.useRemoteBackend,
      localBackendUrl: localBackendUrl ?? this.localBackendUrl,
      remoteBackendUrl: remoteBackendUrl ?? this.remoteBackendUrl,
      runpodApiKey: runpodApiKey ?? this.runpodApiKey,
      runpodPodType: runpodPodType ?? this.runpodPodType,
      idleTimeoutMinutes: idleTimeoutMinutes ?? this.idleTimeoutMinutes,
      defaultWidth: defaultWidth ?? this.defaultWidth,
      defaultHeight: defaultHeight ?? this.defaultHeight,
      defaultSteps: defaultSteps ?? this.defaultSteps,
      defaultCfgScale: defaultCfgScale ?? this.defaultCfgScale,
      defaultScheduler: defaultScheduler ?? this.defaultScheduler,
      defaultBatchSize: defaultBatchSize ?? this.defaultBatchSize,
    );
  }
  
  Map<String, dynamic> toJson() {
    return {
      'useRemoteBackend': useRemoteBackend,
      'localBackendUrl': localBackendUrl,
      'remoteBackendUrl': remoteBackendUrl,
      'runpodApiKey': runpodApiKey,
      'runpodPodType': runpodPodType,
      'idleTimeoutMinutes': idleTimeoutMinutes,
      'defaultWidth': defaultWidth,
      'defaultHeight': defaultHeight,
      'defaultSteps': defaultSteps,
      'defaultCfgScale': defaultCfgScale,
      'defaultScheduler': defaultScheduler,
      'defaultBatchSize': defaultBatchSize,
    };
  }
  
  factory AppSettings.fromJson(Map<String, dynamic> json) {
    return AppSettings(
      useRemoteBackend: json['useRemoteBackend'] ?? false,
      localBackendUrl: json['localBackendUrl'] ?? 'http://localhost:9090',
      remoteBackendUrl: json['remoteBackendUrl'],
      runpodApiKey: json['runpodApiKey'],
      runpodPodType: json['runpodPodType'] ?? 'NVIDIA A5000',
      idleTimeoutMinutes: json['idleTimeoutMinutes'] ?? 30,
      defaultWidth: json['defaultWidth'] ?? 1024,
      defaultHeight: json['defaultHeight'] ?? 1024,
      defaultSteps: json['defaultSteps'] ?? 30,
      defaultCfgScale: json['defaultCfgScale'] ?? 7.5,
      defaultScheduler: json['defaultScheduler'] ?? 'euler',
      defaultBatchSize: json['defaultBatchSize'] ?? 4,
    );
  }
}

// Settings service and provider
class SettingsService extends StateNotifier<AppSettings> {
  final SharedPreferences _prefs;
  
  SettingsService(this._prefs) : super(_loadSettings(_prefs));
  
  static AppSettings _loadSettings(SharedPreferences prefs) {
    final settingsJson = prefs.getString('appSettings');
    if (settingsJson == null) {
      return AppSettings();
    }
    
    try {
      return AppSettings.fromJson(jsonDecode(settingsJson));
    } catch (e) {
      print('Error loading settings: $e');
      return AppSettings();
    }
  }
  
  Future<void> saveSettings() async {
    final settingsJson = jsonEncode(state.toJson());
    await _prefs.setString('appSettings', settingsJson);
  }
  
  void updateUseRemote(bool value) {
    state = state.copyWith(useRemoteBackend: value);
  }
  
  void updateLocalUrl(String value) {
    state = state.copyWith(localBackendUrl: value);
  }
  
  void updateRemoteUrl(String value) {
    state = state.copyWith(remoteBackendUrl: value);
  }
  
  void updateRunpodApiKey(String value) {
    state = state.copyWith(runpodApiKey: value);
  }
  
  void updateRunpodPodType(String value) {
    state = state.copyWith(runpodPodType: value);
  }
  
  void updateIdleTimeout(int value) {
    state = state.copyWith(idleTimeoutMinutes: value);
  }
  
  void updateDefaultWidth(int value) {
    state = state.copyWith(defaultWidth: value);
  }
  
  void updateDefaultHeight(int value) {
    state = state.copyWith(defaultHeight: value);
  }
  
  void updateDefaultSteps(int value) {
    state = state.copyWith(defaultSteps: value);
  }
  
  void updateDefaultCfgScale(double value) {
    state = state.copyWith(defaultCfgScale: value);
  }
  
  void updateDefaultScheduler(String value) {
    state = state.copyWith(defaultScheduler: value);
  }
  
  void updateDefaultBatchSize(int value) {
    state = state.copyWith(defaultBatchSize: value);
  }
  
  Future<List<CostRecord>> getCostHistory() async {
    final historyJson = _prefs.getString('costHistory');
    if (historyJson == null) {
      return [];
    }
    
    try {
      final historyList = jsonDecode(historyJson) as List;
      return historyList.map((item) {
        return CostRecord(
          podId: item['podId'],
          sessionDate: DateTime.parse(item['sessionDate']),
          duration: Duration(seconds: item['durationSeconds']),
          cost: item['cost'].toDouble(),
        );
      }).toList();
    } catch (e) {
      print('Error loading cost history: $e');
      return [];
    }
  }
  
  Future<void> addCostRecord(CostRecord record) async {
    final history = await getCostHistory();
    history.add(record);
    
    final historyJson = jsonEncode(history.map((record) {
      return {
        'podId': record.podId,
        'sessionDate': record.sessionDate.toIso8601String(),
        'durationSeconds': record.duration.inSeconds,
        'cost': record.cost,
      };
    }).toList());
    
    await _prefs.setString('costHistory', historyJson);
  }
  
  Future<void> clearCostHistory() async {
    await _prefs.remove('costHistory');
  }
}

// Provider for settings service
final settingsServiceProvider = Provider<SettingsService>((ref) {
  throw UnimplementedError(
    'Initialize this provider with an override that provides SharedPreferences'
  );
});

// Provider for settings state
final settingsProvider = StateNotifierProvider<SettingsService, AppSettings>((ref) {
  return ref.watch(settingsServiceProvider);
});

// Template settings section widget that can be used in other settings screens
class SettingsSection extends StatelessWidget {
  final String title;
  final List<Widget> children;
  
  const SettingsSection({
    Key? key,
    required this.title,
    required this.children,
  }) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
        SizedBox(height: 16),
        ...children,
      ],
    );
  }
}

class NotificationManager extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final notifications = ref.watch(notificationProvider);
    
    if (notifications.isEmpty) {
      return SizedBox.shrink();
    }
    
    return Stack(
      children: [
        // Position the notifications at the bottom of the screen
        Positioned(
          bottom: 16,
          right: 16,
          width: 300,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              for (final notification in notifications)
                NotificationCard(
                  notification: notification,
                  onDismiss: () => ref.read(notificationProvider.notifier).dismiss(notification.id),
                ),
            ],
          ),
        ),
      ],
    );
  }
}

class NotificationCard extends StatefulWidget {
  final AppNotification notification;
  final VoidCallback onDismiss;
  
  const NotificationCard({
    Key? key,
    required this.notification,
    required this.onDismiss,
  }) : super(key: key);
  
  @override
  _NotificationCardState createState() => _NotificationCardState();
}

class _NotificationCardState extends State<NotificationCard> with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _fadeAnimation;
  late Animation<Offset> _slideAnimation;
  
  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: Duration(milliseconds: 300),
      vsync: this,
    );
    
    _fadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(CurvedAnimation(
      parent: _controller,
      curve: Curves.easeOut,
    ));
    
    _slideAnimation = Tween<Offset>(
      begin: Offset(1.0, 0.0),
      end: Offset.zero,
    ).animate(CurvedAnimation(
      parent: _controller,
      curve: Curves.easeOut,
    ));
    
    _controller.forward();
    
    // Auto-dismiss after duration if specified
    if (widget.notification.autoDismissDuration != null) {
      Future.delayed(widget.notification.autoDismissDuration!, () {
        if (mounted) {
          _dismiss();
        }
      });
    }
  }
  
  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }
  
  void _dismiss() {
    _controller.reverse().then((_) {
      widget.onDismiss();
    });
  }
  
  @override
  Widget build(BuildContext context) {
    return SlideTransition(
      position: _slideAnimation,
      child: FadeTransition(
        opacity: _fadeAnimation,
        child: Card(
          elevation: 4,
          margin: EdgeInsets.only(bottom: 8),
          color: _getNotificationColor(widget.notification.type),
          child: ListTile(
            leading: Icon(
              _getNotificationIcon(widget.notification.type),
              color: Colors.white,
            ),
            title: Text(
              widget.notification.title,
              style: TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.bold,
              ),
            ),
            subtitle: widget.notification.message != null
                ? Text(
                    widget.notification.message!,
                    style: TextStyle(color: Colors.white.withOpacity(0.9)),
                  )
                : null,
            trailing: IconButton(
              icon: Icon(Icons.close, color: Colors.white),
              onPressed: _dismiss,
            ),
            onTap: widget.notification.onTap,
          ),
        ),
      ),
    );
  }
  
  Color _getNotificationColor(NotificationType type) {
    switch (type) {
      case NotificationType.success:
        return Colors.green;
      case NotificationType.info:
        return Colors.blue;
      case NotificationType.warning:
        return Colors.orange;
      case NotificationType.error:
        return Colors.red;
    }
  }
  
  IconData _getNotificationIcon(NotificationType type) {
    switch (type) {
      case NotificationType.success:
        return Icons.check_circle;
      case NotificationType.info:
        return Icons.info;
      case NotificationType.warning:
        return Icons.warning;
      case NotificationType.error:
        return Icons.error;
    }
  }
}

// Notification models and providers
enum NotificationType {
  success,
  info,
  warning,
  error
}

class AppNotification {
  final String id;
  final String title;
  final String? message;
  final NotificationType type;
  final Duration? autoDismissDuration;
  final VoidCallback? onTap;
  
  AppNotification({
    required this.title,
    this.message,
    required this.type,
    this.autoDismissDuration = const Duration(seconds: 5),
    this.onTap,
  }) : id = uuid.v4();
}

class NotificationService extends StateNotifier<List<AppNotification>> {
  NotificationService() : super([]);
  
  void show({
    required String title,
    String? message,
    required NotificationType type,
    Duration? autoDismissDuration,
    VoidCallback? onTap,
  }) {
    final notification = AppNotification(
      title: title,
      message: message,
      type: type,
      autoDismissDuration: autoDismissDuration,
      onTap: onTap,
    );
    
    state = [...state, notification];
  }
  
  void showSuccess(String title, {String? message, VoidCallback? onTap}) {
    show(
      title: title,
      message: message,
      type: NotificationType.success,
      onTap: onTap,
    );
  }
  
  void showInfo(String title, {String? message, VoidCallback? onTap}) {
    show(
      title: title,
      message: message,
      type: NotificationType.info,
      onTap: onTap,
    );
  }
  
  void showWarning(String title, {String? message, VoidCallback? onTap}) {
    show(
      title: title,
      message: message,
      type: NotificationType.warning,
      onTap: onTap,
    );
  }
  
  void showError(String title, {String? message, VoidCallback? onTap}) {
    show(
      title: title,
      message: message,
      type: NotificationType.error,
      autoDismissDuration: null, // Errors don't auto-dismiss
      onTap: onTap,
    );
  }
  
  void dismiss(String id) {
    state = state.where((notification) => notification.id != id).toList();
  }
  
  void dismissAll() {
    state = [];
  }
}

final notificationProvider = StateNotifierProvider<NotificationService, List<AppNotification>>((ref) {
  return NotificationService();
});

class GenerationQueueMonitor extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final queueStatus = ref.watch(queueStatusProvider);
    
    // Don't show anything if there are no active items
    if (queueStatus.pending == 0 && queueStatus.inProgress == 0) {
      return SizedBox.shrink();
    }
    
    return Card(
      margin: EdgeInsets.all(16),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.queue, color: Colors.blue),
                SizedBox(width: 8),
                Text(
                  'Generation Queue',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            
            Divider(),
            
            // Queue statistics
            _buildQueueStatRow(
              context, 
              'Pending', 
              queueStatus.pending, 
              Colors.orange
            ),
            
            _buildQueueStatRow(
              context, 
              'In Progress', 
              queueStatus.inProgress, 
              Colors.blue
            ),
            
            _buildQueueStatRow(
              context, 
              'Completed', 
              queueStatus.completed, 
              Colors.green
            ),
            
            if (queueStatus.failed > 0)
              _buildQueueStatRow(
                context, 
                'Failed', 
                queueStatus.failed, 
                Colors.red
              ),
            
            Divider(),
            
            // Active operations
            if (queueStatus.activeOperations.isNotEmpty)
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Active Operations',
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),
                  SizedBox(height: 8),
                  ...queueStatus.activeOperations.map((op) => 
                    _buildActiveOperationRow(context, op)
                  ),
                ],
              ),
            
            SizedBox(height: 16),
            
            // Actions
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                OutlinedButton.icon(
                  icon: Icon(Icons.refresh),
                  label: Text('Refresh'),
                  onPressed: () => ref.refresh(queueStatusProvider),
                ),
                
                if (queueStatus.pending > 0 || queueStatus.inProgress > 0)
                  Padding(
                    padding: EdgeInsets.only(left: 8),
                    child: OutlinedButton.icon(
                      icon: Icon(Icons.cancel),
                      label: Text('Cancel All'),
                      onPressed: () => _showCancelConfirmation(context, ref),
                      style: OutlinedButton.styleFrom(
                        primary: Colors.red,
                      ),
                    ),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }
  
  Widget _buildQueueStatRow(
    BuildContext context, 
    String label, 
    int count, 
    Color color
  ) {
    return Padding(
      padding: EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Container(
            width: 12,
            height: 12,
            decoration: BoxDecoration(
              color: color,
              shape: BoxShape.circle,
            ),
          ),
          SizedBox(width: 8),
          Text(label, style: TextStyle(color: Colors.grey.shade700)),
          Spacer(),
          Text(
            count.toString(),
            style: TextStyle(
              fontWeight: FontWeight.bold,
              color: count > 0 ? color : Colors.grey,
            ),
          ),
        ],
      ),
    );
  }
  
  Widget _buildActiveOperationRow(
    BuildContext context, 
    QueueOperation operation
  ) {
    return Padding(
      padding: EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          // Operation type icon
          Icon(
            operation.type == QueueOperationType.generation
                ? Icons.image
                : Icons.download,
            size: 16,
            color: Colors.grey,
          ),
          
          SizedBox(width: 8),
          
          // Operation description
          Expanded(
            child: Text(
              operation.description,
              overflow: TextOverflow.ellipsis,
            ),
          ),
          
          SizedBox(width: 16),
          
          // Progress indicator
          if (operation.progress != null)
            Container(
              width: 60,
              child: LinearProgressIndicator(
                value: operation.progress,
                backgroundColor: Colors.grey.shade200,
                valueColor: AlwaysStoppedAnimation(Colors.blue),
              ),
            ),
          
          SizedBox(width: 8),
          
          // Progress text
          if (operation.progress != null)
            Text(
              '${(operation.progress! * 100).toStringAsFixed(0)}%',
              style: TextStyle(fontSize: 12),
            ),
          
          SizedBox(width: 8),
          
          // Cancel button
          IconButton(
            icon: Icon(Icons.close, size: 16),
            onPressed: operation.onCancel,
            padding: EdgeInsets.zero,
            constraints: BoxConstraints(),
            splashRadius: 16,
          ),
        ],
      ),
    );
  }
  
  void _showCancelConfirmation(BuildContext context, WidgetRef ref) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Cancel All Operations?'),
        content: Text(
          'This will cancel all pending and in-progress generation operations. '
          'This action cannot be undone.'
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: Text('No, Keep Processing'),
          ),
          TextButton(
            onPressed: () {
              Navigator.of(context).pop();
              ref.read(generationQueueProvider.notifier).cancelAll();
            },
            child: Text('Yes, Cancel All'),
            style: TextButton.styleFrom(primary: Colors.red),
          ),
        ],
      ),
    );
  }
}

// Queue status provider and related classes
final queueStatusProvider = Provider<QueueStatus>((ref) {
  final sessions = ref.watch(generationSessionProvider).steps;
  final retrievals = ref.watch(retrievalQueueProvider);
  
  int pending = 0;
  int inProgress = 0;
  int completed = 0;
  int failed = 0;
  
  List<QueueOperation> activeOperations = [];
  
  // Count generation operations
  for (final step in sessions) {
    switch (step.status) {
      case 'pending':
        pending++;
        activeOperations.add(
          QueueOperation(
            id: step.id,
            type: QueueOperationType.generation,
            description: 'Generating: ${_truncatePrompt(step.prompt)}',
            progress: null,
            onCancel: () => ref.read(generationStepProvider.notifier)
                .cancelStep(step.id),
          ),
        );
        break;
      case 'processing':
        inProgress++;
        activeOperations.add(
          QueueOperation(
            id: step.id,
            type: QueueOperationType.generation,
            description: 'Generating: ${_truncatePrompt(step.prompt)}',
            progress: step.progress,
            onCancel: () => ref.read(generationStepProvider.notifier)
                .cancelStep(step.id),
          ),
        );
        break;
      case 'completed':
        completed++;
        break;
      case 'failed':
        failed++;
        break;
    }
  }
  
  // Count retrieval operations
  for (final retrieval in retrievals) {
    switch (retrieval.status) {
      case 'pending':
        pending++;
        activeOperations.add(
          QueueOperation(
            id: retrieval.id,
            type: QueueOperationType.retrieval,
            description: 'Retrieving image: ${retrieval.imageId}',
            progress: null,
            onCancel: () => ref.read(retrievalQueueProvider.notifier)
                .cancelRetrieval(retrieval.id),
          ),
        );
        break;
      case 'processing':
        inProgress++;
        activeOperations.add(
          QueueOperation(
            id: retrieval.id,
            type: QueueOperationType.retrieval,
            description: 'Retrieving image: ${retrieval.imageId}',
            progress: retrieval.progress,
            onCancel: () => ref.read(retrievalQueueProvider.notifier)
                .cancelRetrieval(retrieval.id),
          ),
        );
        break;
      // Other statuses are tracked in retrieval-specific monitors
    }
  }
  
  return QueueStatus(
    pending: pending,
    inProgress: inProgress,
    completed: completed,
    failed: failed,
    activeOperations: activeOperations,
  );
});

String _truncatePrompt(String prompt, {int maxLength = 30}) {
  if (prompt.length <= maxLength) return prompt;
  return prompt.substring(0, maxLength - 3) + '...';
}

class QueueStatus {
  final int pending;
  final int inProgress;
  final int completed;
  final int failed;
  final List<QueueOperation> activeOperations;
  
  QueueStatus({
    required this.pending,
    required this.inProgress,
    required this.completed,
    required this.failed,
    required this.activeOperations,
  });
}

enum QueueOperationType {
  generation,
  retrieval
}

class QueueOperation {
  final String id;
  final QueueOperationType type;
  final String description;
  final double? progress;
  final VoidCallback onCancel;
  
  QueueOperation({
    required this.id,
    required this.type,
    required this.description,
    this.progress,
    required this.onCancel,
  });
}

// Generation queue provider for queue management
final generationQueueProvider = StateNotifierProvider<GenerationQueueNotifier, QueueState>((ref) {
  return GenerationQueueNotifier(ref);
});

class QueueState {
  final List<String> pendingStepIds;
  final List<String> processingStepIds;
  
  QueueState({
    this.pendingStepIds = const [],
    this.processingStepIds = const [],
  });
  
  QueueState copyWith({
    List<String>? pendingStepIds,
    List<String>? processingStepIds,
  }) {
    return QueueState(
      pendingStepIds: pendingStepIds ?? this.pendingStepIds,
      processingStepIds: processingStepIds ?? this.processingStepIds,
    );
  }
}

class GenerationQueueNotifier extends StateNotifier<QueueState> {
  final Ref _ref;
  
  GenerationQueueNotifier(this._ref) : super(QueueState());
  
  void addToPending(String stepId) {
    state = state.copyWith(
      pendingStepIds: [...state.pendingStepIds, stepId],
    );
  }
  
  void moveToProcessing(String stepId) {
    state = state.copyWith(
      pendingStepIds: state.pendingStepIds.where((id) => id != stepId).toList(),
      processingStepIds: [...state.processingStepIds, stepId],
    );
  }
  
  void removeFromQueue(String stepId) {
    state = state.copyWith(
      pendingStepIds: state.pendingStepIds.where((id) => id != stepId).toList(),
      processingStepIds: state.processingStepIds.where((id) => id != stepId).toList(),
    );
  }
  
  void cancelStep(String stepId) {
    final stepNotifier = _ref.read(generationStepProvider.notifier);
    stepNotifier.cancelStep(stepId);
    removeFromQueue(stepId);
  }
  
  void cancelAll() {
    // Cancel all pending steps
    for (final stepId in state.pendingStepIds) {
      _ref.read(generationStepProvider.notifier).cancelStep(stepId);
    }
    
    // Try to cancel processing steps (may or may not work depending on state)
    for (final stepId in state.processingStepIds) {
      _ref.read(generationStepProvider.notifier).cancelStep(stepId);
    }
    
    // Clear the queue
    state = QueueState();
  }
}

class BackendStatusWidget extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final backendStatus = ref.watch(backendStatusProvider);
    
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(8.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Backend Status',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 8),
            _buildStatusRow(
              context,
              'Connection:',
              backendStatus.isConnected ? 'Connected' : 'Disconnected',
              backendStatus.isConnected ? Colors.green : Colors.red,
            ),
            _buildStatusRow(
              context,
              'Mode:',
              backendStatus.isRemote ? 'Remote' : 'Local',
              Colors.blue,
            ),
            if (backendStatus.isRemote) ...[
              _buildStatusRow(
                context,
                'Pod Status:',
                backendStatus.podStatus ?? 'Unknown',
                _getPodStatusColor(backendStatus.podStatus),
              ),
              if (backendStatus.currentCost != null)
                _buildStatusRow(
                  context,
                  'Current Cost:',
                  '\$${backendStatus.currentCost!.toStringAsFixed(2)}',
                  Colors.orange,
                ),
              if (backendStatus.uptime != null)
                _buildStatusRow(
                  context,
                  'Uptime:',
                  _formatDuration(backendStatus.uptime!),
                  Colors.blue,
                ),
            ],
            SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                // Mode switch
                OutlinedButton.icon(
                  icon: Icon(backendStatus.isRemote ? Icons.computer : Icons.cloud),
                  label: Text(backendStatus.isRemote ? 'Switch to Local' : 'Switch to Remote'),
                  onPressed: () => ref.read(backendManagerProvider).switchMode(!backendStatus.isRemote),
                ),
                
                SizedBox(width: 8),
                
                // Connect/disconnect button
                if (backendStatus.isRemote)
                  ElevatedButton.icon(
                    icon: Icon(backendStatus.isConnected ? Icons.stop : Icons.play_arrow),
                    label: Text(backendStatus.isConnected ? 'Stop Pod' : 'Start Pod'),
                    style: ElevatedButton.styleFrom(
                      primary: backendStatus.isConnected ? Colors.red : Colors.green,
                    ),
                    onPressed: () {
                      if (backendStatus.isConnected) {
                        ref.read(backendManagerProvider).stopPod();
                      } else {
                        ref.read(backendManagerProvider).startPod();
                      }
                    },
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }
  
  Widget _buildStatusRow(BuildContext context, String label, String value, Color color) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4.0),
      child: Row(
        children: [
          Text(label, style: TextStyle(fontWeight: FontWeight.w500)),
          SizedBox(width: 8),
          Text(
            value,
            style: TextStyle(color: color, fontWeight: FontWeight.w500),
          ),
        ],
      ),
    );
  }
  
  Color _getPodStatusColor(String? status) {
    if (status == null) return Colors.grey;
    
    switch (status.toUpperCase()) {
      case 'RUNNING':
        return Colors.green;
      case 'STARTING':
        return Colors.orange;
      case 'STOPPED':
        return Colors.red;
      case 'ERROR':
        return Colors.red.shade700;
      default:
        return Colors.grey;
    }
  }
  
  String _formatDuration(Duration duration) {
    final hours = duration.inHours;
    final minutes = duration.inMinutes % 60;
    
    if (hours > 0) {
      return '$hours hr ${minutes} min';
    } else {
      return '${minutes} min';
    }
  }
}

// Extended view with more details
class DetailedBackendStatusWidget extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final backendStatus = ref.watch(backendStatusProvider);
    final costHistory = ref.watch(costHistoryProvider);
    
    return Card(
      margin: EdgeInsets.all(16),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'InvokeAI Backend',
              style: Theme.of(context).textTheme.headline6,
            ),
            
            SizedBox(height: 16),
            
            // Connection status card
            _buildConnectionStatusCard(context, backendStatus),
            
            SizedBox(height: 16),
            
            // Remote pod details (if in remote mode)
            if (backendStatus.isRemote)
              _buildRemotePodDetails(context, backendStatus),
            
            // Action buttons
            SizedBox(height: 16),
            _buildActionButtons(context, ref, backendStatus),
            
            // Cost history (if available)
            if (backendStatus.isRemote && costHistory.isNotEmpty)
              _buildCostHistory(context, costHistory),
          ],
        ),
      ),
    );
  }
  
  Widget _buildConnectionStatusCard(BuildContext context, BackendStatus status) {
    return Container(
      padding: EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: status.isConnected ? Colors.green.withOpacity(0.1) : Colors.red.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: status.isConnected ? Colors.green : Colors.red,
          width: 1,
        ),
      ),
      child: Row(
        children: [
          Icon(
            status.isConnected ? Icons.check_circle : Icons.error,
            color: status.isConnected ? Colors.green : Colors.red,
            size: 48,
          ),
          SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  status.isConnected ? 'Connected' : 'Disconnected',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: status.isConnected ? Colors.green : Colors.red,
                  ),
                ),
                SizedBox(height: 4),
                Text(
                  'Mode: ${status.isRemote ? 'Remote' : 'Local'}',
                  style: TextStyle(fontSize: 14),
                ),
                Text(
                  'URL: ${status.baseUrl}',
                  style: TextStyle(fontSize: 14),
                  overflow: TextOverflow.ellipsis,
                ),
                if (status.apiVersion != null)
                  Text(
                    'API Version: ${status.apiVersion}',
                    style: TextStyle(fontSize: 14),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }
  
  Widget _buildRemotePodDetails(BuildContext context, BackendStatus status) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Remote Pod Details',
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
          ),
        ),
        SizedBox(height: 8),
        Table(
          columnWidths: {
            0: FlexColumnWidth(1),
            1: FlexColumnWidth(2),
          },
          children: [
            TableRow(
              children: [
                Padding(
                  padding: EdgeInsets.symmetric(vertical: 4),
                  child: Text('Pod ID:'),
                ),
                Padding(
                  padding: EdgeInsets.symmetric(vertical: 4),
                  child: Text(status.podId ?? 'N/A'),
                ),
              ],
            ),
            TableRow(
              children: [
                Padding(
                  padding: EdgeInsets.symmetric(vertical: 4),
                  child: Text('Status:'),
                ),
                Padding(
                  padding: EdgeInsets.symmetric(vertical: 4),
                  child: Text(
                    status.podStatus ?? 'Unknown',
                    style: TextStyle(
                      color: _getPodStatusColor(status.podStatus),
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
            if (status.lastActivity != null)
              TableRow(
                children: [
                  Padding(
                    padding: EdgeInsets.symmetric(vertical: 4),
                    child: Text('Last Activity:'),
                  ),
                  Padding(
                    padding: EdgeInsets.symmetric(vertical: 4),
                    child: Text(_formatDateTime(status.lastActivity!)),
                  ),
                ],
              ),
            if (status.uptime != null)
              TableRow(
                children: [
                  Padding(
                    padding: EdgeInsets.symmetric(vertical: 4),
                    child: Text('Uptime:'),
                  ),
                  Padding(
                    padding: EdgeInsets.symmetric(vertical: 4),
                    child: Text(_formatDuration(status.uptime!)),
                  ),
                ],
              ),
            if (status.currentCost != null)
              TableRow(
                children: [
                  Padding(
                    padding: EdgeInsets.symmetric(vertical: 4),
                    child: Text('Current Cost:'),
                  ),
                  Padding(
                    padding: EdgeInsets.symmetric(vertical: 4),
                    child: Text(
                      '\$${status.currentCost!.toStringAsFixed(2)}',
                      style: TextStyle(
                        color: Colors.orange,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ],
              ),
          ],
        ),
      ],
    );
  }
  
  Widget _buildActionButtons(
    BuildContext context, 
    WidgetRef ref, 
    BackendStatus status
  ) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.end,
      children: [
        // Refresh status button
        OutlinedButton.icon(
          icon: Icon(Icons.refresh),
          label: Text('Refresh Status'),
          onPressed: () => ref.refresh(backendStatusProvider),
        ),
        
        SizedBox(width: 8),
        
        // Mode switch button
        OutlinedButton.icon(
          icon: Icon(status.isRemote ? Icons.computer : Icons.cloud),
          label: Text(status.isRemote ? 'Switch to Local' : 'Switch to Remote'),
          onPressed: () => ref.read(backendManagerProvider).switchMode(!status.isRemote),
        ),
        
        SizedBox(width: 8),
        
        // Connect/disconnect button (remote mode only)
        if (status.isRemote)
          ElevatedButton.icon(
            icon: Icon(status.isConnected ? Icons.stop : Icons.play_arrow),
            label: Text(status.isConnected ? 'Stop Pod' : 'Start Pod'),
            style: ElevatedButton.styleFrom(
              primary: status.isConnected ? Colors.red : Colors.green,
            ),
            onPressed: () {
              if (status.isConnected) {
                ref.read(backendManagerProvider).stopPod();
              } else {
                ref.read(backendManagerProvider).startPod();
              }
            },
          ),
      ],
    );
  }
  
  Widget _buildCostHistory(BuildContext context, List<CostRecord> history) {
    // Calculate total cost
    final totalCost = history.fold<double>(
      0, (sum, record) => sum + record.cost
    );
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(height: 24),
        Text(
          'Cost History',
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
          ),
        ),
        SizedBox(height: 8),
        Card(
          child: Padding(
            padding: EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                Text(
                  'Total Spend: \${totalCost.toStringAsFixed(2)}',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: Colors.orange,
                  ),
                ),
                SizedBox(height: 16),
                
                // Cost history list (last 5 sessions)
                ListView.builder(
                  shrinkWrap: true,
                  physics: NeverScrollableScrollPhysics(),
                  itemCount: history.length > 5 ? 5 : history.length,
                  itemBuilder: (context, index) {
                    final record = history[index];
                    return ListTile(
                      leading: Icon(Icons.access_time),
                      title: Text('Session on ${_formatDate(record.sessionDate)}'),
                      subtitle: Text('Duration: ${_formatDuration(record.duration)}'),
                      trailing: Text(
                        '\${record.cost.toStringAsFixed(2)}',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          color: Colors.orange,
                        ),
                      ),
                    );
                  },
                ),
                
                if (history.length > 5) ...[
                  SizedBox(height: 8),
                  TextButton(
                    onPressed: () => _showFullCostHistory(context, history),
                    child: Text('View Full History'),
                  ),
                ],
              ],
            ),
          ),
        ),
      ],
    );
  }
  
  void _showFullCostHistory(BuildContext context, List<CostRecord> history) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Cost History'),
        content: Container(
          width: double.maxFinite,
          child: ListView.builder(
            shrinkWrap: true,
            itemCount: history.length,
            itemBuilder: (context, index) {
              final record = history[index];
              return ListTile(
                title: Text('Session on ${_formatDate(record.sessionDate)}'),
                subtitle: Text('Duration: ${_formatDuration(record.duration)}'),
                trailing: Text(
                  '\${record.cost.toStringAsFixed(2)}',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    color: Colors.orange,
                  ),
                ),
              );
            },
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: Text('Close'),
          ),
        ],
      ),
    );
  }
  
  String _formatDate(DateTime date) {
    return '${date.month}/${date.day}/${date.year}';
  }
  
  String _formatDateTime(DateTime dateTime) {
    final now = DateTime.now();
    final difference = now.difference(dateTime);
    
    if (difference.inDays < 1) {
      if (difference.inHours < 1) {
        if (difference.inMinutes < 1) {
          return 'Just now';
        }
        return '${difference.inMinutes} minute${difference.inMinutes > 1 ? 's' : ''} ago';
      }
      return '${difference.inHours} hour${difference.inHours > 1 ? 's' : ''} ago';
    } else if (difference.inDays < 7) {
      return '${difference.inDays} day${difference.inDays > 1 ? 's' : ''} ago';
    } else {
      return _formatDate(dateTime);
    }
  }
  
  String _formatDuration(Duration duration) {
    final hours = duration.inHours;
    final minutes = duration.inMinutes % 60;
    
    if (hours > 0) {
      return '$hours hr ${minutes} min';
    } else {
      return '${minutes} min';
    }
  }
  
  Color _getPodStatusColor(String? status) {
    if (status == null) return Colors.grey;
    
    switch (status.toUpperCase()) {
      case 'RUNNING':
        return Colors.green;
      case 'STARTING':
        return Colors.orange;
      case 'STOPPED':
        return Colors.red;
      case 'ERROR':
        return Colors.red.shade700;
      default:
        return Colors.grey;
    }
  }
}

// Cost history provider
final costHistoryProvider = FutureProvider<List<CostRecord>>((ref) async {
  final settingsService = ref.watch(settingsServiceProvider);
  return settingsService.getCostHistory();
});

// Cost record class
class CostRecord {
  final String podId;
  final DateTime sessionDate;
  final Duration duration;
  final double cost;
  
  CostRecord({
    required this.podId,
    required this.sessionDate,
    required this.duration,
    required this.cost,
  });
}

class RetrievalStatusWidget extends ConsumerWidget {
  final String stepId;
  
  const RetrievalStatusWidget({
    Key? key, 
    required this.stepId,
  }) : super(key: key);
  
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final status = ref.watch(retrievalStatusProvider(stepId));
    
    // Don't show anything if there are no retrievals or all are complete
    if (status.total == 0 || (status.isComplete && !status.hasFailures)) {
      return SizedBox.shrink();
    }
    
    return Card(
      margin: EdgeInsets.all(16),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  status.hasFailures 
                    ? Icons.error_outline 
                    : Icons.download_rounded,
                  color: status.hasFailures ? Colors.red : Colors.blue,
                ),
                SizedBox(width: 8),
                Text(
                  'Image Retrieval Status',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                Spacer(),
                Text(
                  '${status.completed} of ${status.total} images retrieved',
                  style: TextStyle(
                    color: status.hasFailures ? Colors.red : Colors.blue,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ],
            ),
            
            SizedBox(height: 12),
            
            // Progress bar
            ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                value: status.progressPercentage / 100,
                backgroundColor: Colors.grey.shade200,
                valueColor: AlwaysStoppedAnimation(
                  status.hasFailures ? Colors.orange : Colors.blue,
                ),
                minHeight: 8,
              ),
            ),
            
            SizedBox(height: 12),
            
            // Additional status details
            _buildStatusDetails(context, status),
            
            // Action buttons for failed retrievals
            if (status.hasFailures) ...[
              SizedBox(height: 12),
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  OutlinedButton.icon(
                    icon: Icon(Icons.refresh),
                    label: Text('Retry Failed'),
                    onPressed: () => _retryFailedRetrievals(context, ref),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }
  
  Widget _buildStatusDetails(BuildContext context, RetrievalStatus status) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
      children: [
        _buildStatusItem(
          context, 
          'Completed', 
          status.completed.toString(), 
          Colors.green
        ),
        _buildStatusItem(
          context, 
          'Pending', 
          status.pending.toString(), 
          Colors.blue
        ),
        if (status.hasFailures)
          _buildStatusItem(
            context, 
            'Failed', 
            status.failed.toString(), 
            Colors.red
          ),
      ],
    );
  }
  
  Widget _buildStatusItem(
    BuildContext context, 
    String label, 
    String value, 
    Color color
  ) {
    return Column(
      children: [
        Text(
          label,
          style: TextStyle(
            color: Colors.grey.shade600,
            fontSize: 12,
          ),
        ),
        SizedBox(height: 4),
        Container(
          width: 32,
          height: 32,
          decoration: BoxDecoration(
            color: color.withOpacity(0.1),
            shape: BoxShape.circle,
            border: Border.all(color: color, width: 2),
          ),
          child: Center(
            child: Text(
              value,
              style: TextStyle(
                color: color,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ),
      ],
    );
  }
  
  void _retryFailedRetrievals(BuildContext context, WidgetRef ref) {
    ref.read(generationStepProvider.notifier).retryFailedRetrievals(stepId);
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Retrying failed image retrievals...'),
        duration: Duration(seconds: 2),
      ),
    );
  }
}

// Detailed retrieval info widget for the alternatives view
class RetrievalInfoWidget extends ConsumerWidget {
  final String stepId;
  
  const RetrievalInfoWidget({
    Key? key,
    required this.stepId,
  }) : super(key: key);
  
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final status = ref.watch(retrievalStatusProvider(stepId));
    final step = ref.watch(generationStepProvider).currentStep;
    
    if (step == null || status.total == 0) {
      return SizedBox.shrink();
    }
    
    return ExpansionTile(
      title: Text('Retrieval Details'),
      initiallyExpanded: status.hasFailures,
      leading: Icon(
        status.hasFailures ? Icons.error_outline : Icons.info_outline,
        color: status.hasFailures ? Colors.red : Colors.blue,
      ),
      children: [
        Padding(
          padding: EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Image Retrieval Status',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              SizedBox(height: 8),
              
              // Status rows
              _buildStatusRow(
                'Completed', 
                status.completed, 
                status.total, 
                Colors.green
              ),
              _buildStatusRow(
                'Pending', 
                status.pending, 
                status.total, 
                Colors.blue
              ),
              _buildStatusRow(
                'Failed', 
                status.failed, 
                status.total, 
                Colors.red
              ),
              
              SizedBox(height: 16),
              
              // Correlation ID info
              if (step.correlationId != null) ...[
                Text(
                  'Correlation ID:',
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
                SizedBox(height: 4),
                SelectableText(
                  step.correlationId!,
                  style: TextStyle(fontFamily: 'monospace'),
                ),
              ],
              
              SizedBox(height: 16),
              
              // Batch info
              Text(
                'Batch Information:',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              SizedBox(height: 4),
              Text('Batch ID: ${step.batch_id}'),
              Text('Created: ${_formatDateTime(step.created_at)}'),
              Text('Status: ${step.status}'),
              
              if (status.hasFailures) ...[
                SizedBox(height: 16),
                Center(
                  child: ElevatedButton.icon(
                    icon: Icon(Icons.refresh),
                    label: Text('Retry Failed Retrievals'),
                    onPressed: () => ref.read(generationStepProvider.notifier)
                        .retryFailedRetrievals(stepId),
                  ),
                ),
              ],
            ],
          ),
        ),
      ],
    );
  }
  
  Widget _buildStatusRow(String label, int count, int total, Color color) {
    final percentage = total > 0 ? (count / total * 100).toStringAsFixed(0) : '0';
    
    return Padding(
      padding: EdgeInsets.symmetric(vertical: 4),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('$label:'),
              Text(
                '$count / $total ($percentage%)',
                style: TextStyle(color: color, fontWeight: FontWeight.w500),
              ),
            ],
          ),
          SizedBox(height: 4),
          ClipRRect(
            borderRadius: BorderRadius.circular(2),
            child: LinearProgressIndicator(
              value: total > 0 ? count / total : 0,
              backgroundColor: Colors.grey.shade200,
              valueColor: AlwaysStoppedAnimation(color),
              minHeight: 4,
            ),
          ),
        ],
      ),
    );
  }
  
  String _formatDateTime(DateTime dateTime) {
    final now = DateTime.now();
    final difference = now.difference(dateTime);
    
    if (difference.inDays < 1) {
      if (difference.inHours < 1) {
        if (difference.inMinutes < 1) {
          return 'Just now';
        }
        return '${difference.inMinutes} minute${difference.inMinutes > 1 ? 's' : ''} ago';
      }
      return '${difference.inHours} hour${difference.inHours > 1 ? 's' : ''} ago';
    } else if (difference.inDays < 7) {
      return '${difference.inDays} day${difference.inDays > 1 ? 's' : ''} ago';
    } else {
      final date = dateTime.toLocal();
      return '${date.month}/${date.day}/${date.year}';
    }
  }
}

class AlternativesGridWidget extends ConsumerWidget {
  final GenerationStep step;
  final List<StepAlternative> alternatives;
  
  const AlternativesGridWidget({
    Key? key,
    required this.step,
    required this.alternatives,
  }) : super(key: key);
  
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Header with info
        Padding(
          padding: const EdgeInsets.all(8.0),
          child: Row(
            children: [
              Text(
                'Select an image to continue',
                style: Theme.of(context).textTheme.headline6,
              ),
              Spacer(),
              TextButton.icon(
                icon: Icon(Icons.delete_outline),
                label: Text('Discard All'),
                onPressed: () => _showDiscardDialog(context, ref),
              ),
            ],
          ),
        ),
        
        // Grid of alternatives
        Expanded(
          child: GridView.builder(
            gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 2,
              childAspectRatio: 1.0,
              crossAxisSpacing: 10,
              mainAxisSpacing: 10,
            ),
            itemCount: alternatives.length,
            itemBuilder: (context, index) {
              final alternative = alternatives[index];
              return _buildAlternativeItem(context, ref, alternative);
            },
          ),
        ),
        
        // Generation info
        Padding(
          padding: const EdgeInsets.all(8.0),
          child: Card(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Generation Info', style: TextStyle(fontWeight: FontWeight.bold)),
                  SizedBox(height: 8),
                  Text('Prompt: ${step.prompt}'),
                  if (step.negative_prompt != null && step.negative_prompt!.isNotEmpty)
                    Text('Negative Prompt: ${step.negative_prompt}'),
                  SizedBox(height: 8),
                  Text('Model: ${step.model_key}'),
                  Text('Steps: ${step.parameters['steps']}'),
                  Text('CFG Scale: ${step.parameters['cfg_scale']}'),
                  Text('Scheduler: ${step.parameters['scheduler']}'),
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }
  
  Widget _buildAlternativeItem(BuildContext context, WidgetRef ref, StepAlternative alternative) {
    return GestureDetector(
      onTap: () => _selectAlternative(context, ref, alternative),
      child: Card(
        elevation: 3,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
          side: BorderSide(
            color: alternative.selected 
                ? Theme.of(context).primaryColor 
                : Colors.transparent,
            width: 2,
          ),
        ),
        child: Column(
          children: [
            Expanded(
              child: ClipRRect(
                borderRadius: BorderRadius.vertical(top: Radius.circular(8)),
                child: ProgressiveImageWidget(
                  photoId: alternative.image_id,
                  enableAnimation: true,
                ),
              ),
            ),
            Container(
              padding: EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: Theme.of(context).primaryColor.withOpacity(0.1),
                borderRadius: BorderRadius.vertical(bottom: Radius.circular(8)),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  alternative.selected
                      ? Text('Selected', style: TextStyle(fontWeight: FontWeight.bold))
                      : Text('Tap to select'),
                  IconButton(
                    icon: Icon(alternative.selected ? Icons.check_circle : Icons.check_circle_outline),
                    color: alternative.selected ? Theme.of(context).primaryColor : Colors.grey,
                    onPressed: () => _selectAlternative(context, ref, alternative),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
  
  void _selectAlternative(BuildContext context, WidgetRef ref, StepAlternative alternative) {
    // Check if trying to reselect already selected alternative
    if (alternative.selected) return;
    
    // Check if this would cause history loss
    final hasSubsequentSteps = ref.read(generationSessionProvider).steps
        .any((s) => s.parent_id == step.id);
    
    if (hasSubsequentSteps) {
      showDialog(
        context: context,
        builder: (context) => AlertDialog(
          title: Text('Confirm Selection'),
          content: Text(
            'Selecting a different image will delete all subsequent steps. '
            'Are you sure you want to continue?'
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: Text('Cancel'),
            ),
            TextButton(
              onPressed: () {
                Navigator.of(context).pop();
                ref.read(generationStepProvider.notifier).selectAlternative(
                  step.id,
                  alternative.image_id,
                );
              },
              child: Text('Confirm'),
            ),
          ],
        ),
      );
    } else {
      // No history loss, directly select
      ref.read(generationStepProvider.notifier).selectAlternative(
        step.id,
        alternative.image_id,
      );
    }
  }
  
  void _showDiscardDialog(BuildContext context, WidgetRef ref) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Discard All Images?'),
        content: Text(
          'This will discard all generated images and return to the editor. '
          'This action cannot be undone.'
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: Text('Cancel'),
          ),
          TextButton(
            onPressed: () {
              Navigator.of(context).pop();
              ref.read(generationStepProvider.notifier).discardStep(step.id);
            },
            child: Text('Discard All'),
            style: TextButton.styleFrom(primary: Colors.red),
          ),
        ],
      ),
    );
  }
}

```
// Comparison mode enum and provider
enum ComparisonMode {
  sideBySide,
  slider,
  overlay
}

final comparisonModeProvider = StateProvider<ComparisonMode>((ref) {
  return ComparisonMode.sideBySide;
});
```

### 4. Retrieval Status Manager

This component has been covered in the Status and Retrieval Components section above.

### 5. Model Selection Interface

This component has been covered in the earlier sections.

### 6. Generation Queue Monitor
```dart
class GenerationQueueMonitor extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final queueStatus = ref.watch(queueStatusProvider);
    
    // Don't show anything if there are no active items
    if (queueStatus.pending == 0 && queueStatus.inProgress == 0) {
      return SizedBox.shrink();
    }
    
    return Card(
      margin: EdgeInsets.all(16),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.queue, color: Colors.blue),
                SizedBox(width: 8),
                Text(
                  'Generation Queue',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            
            Divider(),
            
            // Queue statistics
            _buildQueueStatRow(
              context, 
              'Pending', 
              queueStatus.pending, 
              Colors.orange
            ),
            
            _buildQueueStatRow(
              context, 
              'In Progress', 
              queueStatus.inProgress, 
              Colors.blue
            ),
            
            _buildQueueStatRow(
              context, 
              'Completed', 
              queueStatus.completed, 
              Colors.green
            ),
            
            if (queueStatus.failed > 0)
              _buildQueueStatRow(
                context, 
                'Failed', 
                queueStatus.failed, 
                Colors.red
              ),
            
            Divider(),
            
            // Active operations
            if (queueStatus.activeOperations.isNotEmpty)
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Active Operations',
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),
                  SizedBox(height: 8),
                  ...queueStatus.activeOperations.map((op) => 
                    _buildActiveOperationRow(context, op)
                  ),
                ],
              ),
            
            SizedBox(height: 16),
            
            // Actions
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                OutlinedButton.icon(
                  icon: Icon(Icons.refresh),
                  label: Text('Refresh'),
                  onPressed: () => ref.refresh(queueStatusProvider),
                ),
                
                if (queueStatus.pending > 0 || queueStatus.inProgress > 0)
                  Padding(
                    padding: EdgeInsets.only(left: 8),
                    child: OutlinedButton.icon(
                      icon: Icon(Icons.cancel),
                      label: Text('Cancel All'),
                      onPressed: () => _showCancelConfirmation(context, ref),
                      style: OutlinedButton.styleFrom(
                        primary: Colors.red,
                      ),
                    ),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }
  
  Widget _buildQueueStatRow(
    BuildContext context, 
    String label, 
    int count, 
    Color color
  ) {
    return Padding(
      padding: EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Container(
            width: 12,
            height: 12,
            decoration: BoxDecoration(
              color: color,
              shape: BoxShape.circle,
            ),
          ),
          SizedBox(width: 8),
          Text(label, style: TextStyle(color: Colors.grey.shade700)),
          Spacer(),
          Text(
            count.toString(),
            style: TextStyle(
              fontWeight: FontWeight.bold,
              color: count > 0 ? color : Colors.grey,
            ),
          ),
        ],
      ),
    );
  }
  
  Widget _buildActiveOperationRow(
    BuildContext context, 
    QueueOperation operation
  ) {
    return Padding(
      padding: EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          // Operation type icon
          Icon(
            operation.type == QueueOperationType.generation
                ? Icons.image
                : Icons.download,
            size: 16,
            color: Colors.grey,
          ),
          
          SizedBox(width: 8),
          
          // Operation description
          Expanded(
            child: Text(
              operation.description,
              overflow: TextOverflow.ellipsis,
            ),
          ),
          
          SizedBox(width: 16),
          
          // Progress indicator
          if (operation.progress != null)
            Container(
              width: 60,
              child: LinearProgressIndicator(
                value: operation.progress,
                backgroundColor: Colors.grey.shade200,
                valueColor: AlwaysStoppedAnimation(Colors.blue),
              ),
            ),
          
          SizedBox(width: 8),
          
          // Progress text
          if (operation.progress != null)
            Text(
              '${(operation.progress! * 100).toStringAsFixed(0)}%',
              style: TextStyle(fontSize: 12),
            ),
          
          SizedBox(width: 8),
          
          // Cancel button
          IconButton(
            icon: Icon(Icons.close, size: 16),
            onPressed: operation.onCancel,
            padding: EdgeInsets.zero,
            constraints: BoxConstraints(),
            splashRadius: 16,
          ),
        ],
      ),
    );
  }
  
  void _showCancelConfirmation(BuildContext context, WidgetRef ref) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Cancel All Operations?'),
        content: Text(
          'This will cancel all pending and in-progress generation operations. '
          'This action cannot be undone.'
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: Text('No, Keep Processing'),
          ),
          TextButton(
            onPressed: () {
              Navigator.of(context).pop();
              ref.read(generationQueueProvider.notifier).cancelAll();
            },
            child: Text('Yes, Cancel All'),
            style: TextButton.styleFrom(primary: Colors.red),
          ),
        ],
      ),
    );
  }
}

// Queue status provider and related classes
final queueStatusProvider = Provider<QueueStatus>((ref) {
  final sessions = ref.watch(generationSessionProvider).steps;
  final retrievals = ref.watch(retrievalQueueProvider);
  
  int pending = 0;
  int inProgress = 0;
  int completed = 0;
  int failed = 0;
  
  List<QueueOperation> activeOperations = [];
  
  // Count generation operations
  for (final step in sessions) {
    switch (step.status) {
      case 'pending':
        pending++;
        activeOperations.add(
          QueueOperation(
            id: step.id,
            type: QueueOperationType.generation,
            description: 'Generating: ${_truncatePrompt(step.prompt)}',
            progress: null,
            onCancel: () => ref.read(generationStepProvider.notifier)
                .cancelStep(step.id),
          ),
        );
        break;
      case 'processing':
        inProgress++;
        activeOperations.add(
          QueueOperation(
            id: step.id,
            type: QueueOperationType.generation,
            description: 'Generating: ${_truncatePrompt(step.prompt)}',
            progress: step.progress,
            onCancel: () => ref.read(generationStepProvider.notifier)
                .cancelStep(step.id),
          ),
        );
        break;
      case 'completed':
        completed++;
        break;
      case 'failed':
        failed++;
        break;
    }
  }
  
  // Count retrieval operations
  for (final retrieval in retrievals) {
    switch (retrieval.status) {
      case 'pending':
        pending++;
        activeOperations.add(
          QueueOperation(
            id: retrieval.id,
            type: QueueOperationType.retrieval,
            description: 'Retrieving image: ${retrieval.imageId}',
            progress: null,
            onCancel: () => ref.read(retrievalQueueProvider.notifier)
                .cancelRetrieval(retrieval.id),
          ),
        );
        break;
      case 'processing':
        inProgress++;
        activeOperations.add(
          QueueOperation(
            id: retrieval.id,
            type: QueueOperationType.retrieval,
            description: 'Retrieving image: ${retrieval.imageId}',
            progress: retrieval.progress,
            onCancel: () => ref.read(retrievalQueueProvider.notifier)
                .cancelRetrieval(retrieval.id),
          ),
        );
        break;
      // Other statuses are tracked in retrieval-specific monitors
    }
  }
  
  return QueueStatus(
    pending: pending,
    inProgress: inProgress,
    completed: completed,
    failed: failed,
    activeOperations: activeOperations,
  );
});

String _truncatePrompt(String prompt, {int maxLength = 30}) {
  if (prompt.length <= maxLength) return prompt;
  return prompt.substring(0, maxLength - 3) + '...';
}

class QueueStatus {
  final int pending;
  final int inProgress;
  final int completed;
  final int failed;
  final List<QueueOperation> activeOperations;
  
  QueueStatus({
    required this.pending,
    required this.inProgress,
    required this.completed,
    required this.failed,
    required this.activeOperations,
  });
}

enum QueueOperationType {
  generation,
  retrieval
}

class QueueOperation {
  final String id;
  final QueueOperationType type;
  final String description;
  final double? progress;
  final VoidCallback onCancel;
  
  QueueOperation({
    required this.id,
    required this.type,
    required this.description,
    this.progress,
    required this.onCancel,
  });
}
```

### 7. Session Completion Dialog
```dart
class SessionCompletionDialog extends ConsumerWidget {
  final String sessionId;
  
  const SessionCompletionDialog({Key? key, required this.sessionId}) : super(key: key);
  
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final sessionAsync = ref.watch(sessionProvider(sessionId));
    
    return Dialog(
      insetPadding: EdgeInsets.all(16),
      child: Container(
        constraints: BoxConstraints(
          maxWidth: 800,
          maxHeight: MediaQuery.of(context).size.height * 0.9,
        ),
        child: sessionAsync.when(
          data: (session) => _buildContent(context, ref, session),
          loading: () => Center(child: CircularProgressIndicator()),
          error: (error, _) => Center(
            child: Text('Error loading session: $error'),
          ),
        ),
      ),
    );
  }
  
  Widget _buildContent(
    BuildContext context, 
    WidgetRef ref, 
    GenerationSession session
  ) {
    // Selected images from this session
    final selectedImages = session.selectedImages;
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        // Header
        Padding(
          padding: EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Session Complete',
                style: Theme.of(context).textTheme.headline5,
              ),
              SizedBox(height: 8),
              Text(
                'You generated ${session.total_images_generated} images '
                'across ${session.steps_count} steps',
                style: TextStyle(color: Colors.grey.shade700),
              ),
            ],
          ),
        ),
        
        Divider(),
        
        // Session statistics
        Padding(
          padding: EdgeInsets.all(16),
          child: _buildStatisticCards(context, session),
        ),
        
        // Selected images grid
        Expanded(
          child: Padding(
            padding: EdgeInsets.symmetric(horizontal: 16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Selected Images',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 18,
                  ),
                ),
                SizedBox(height: 8),
                Expanded(
                  child: selectedImages.isEmpty
                      ? _buildNoImagesMessage(context)
                      : GridView.builder(
                          gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                            crossAxisCount: 3,
                            childAspectRatio: 1.0,
                            crossAxisSpacing: 10,
                            mainAxisSpacing: 10,
                          ),
                          itemCount: selectedImages.length,
                          itemBuilder: (context, index) {
                            final image = selectedImages[index];
                            return _buildImageTile(context, ref, image);
                          },
                        ),
                ),
              ],
            ),
          ),
        ),
        
        Divider(),
        
        // Action buttons
        Padding(
          padding: EdgeInsets.all(16),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              // Create album option
              if (selectedImages.isNotEmpty)
                OutlinedButton.icon(
                  icon: Icon(Icons.photo_album),
                  label: Text('Create Album'),
                  onPressed: () => _showCreateAlbumDialog(context, ref, selectedImages),
                ),
                
              SizedBox(width: 8),
              
              // Close dialog
              ElevatedButton(
                onPressed: () => Navigator.of(context).pop(),
                child: Text('Done'),
              ),
            ],
          ),
        ),
      ],
    );
  }
  
  Widget _buildStatisticCards(BuildContext context, GenerationSession session) {
    return Row(
      children: [
        _buildStatCard(
          context,
          Icons.image,
          'Total Images',
          session.total_images_generated.toString(),
          Colors.blue,
        ),
        SizedBox(width: 16),
        _buildStatCard(
          context,
          Icons.check_circle,
          'Selected',
          session.selectedImages.length.toString(),
          Colors.green,
        ),
        SizedBox(width: 16),
        _buildStatCard(
          context,
          Icons.layers,
          'Steps',
          session.steps_count.toString(),
          Colors.orange,
        ),
        SizedBox(width: 16),
        _buildStatCard(
          context,
          Icons.timer,
          'Duration',
          _formatDuration(session.duration),
          Colors.purple,
        ),
      ],
    );
  }
  
  Widget _buildStatCard(
    BuildContext context, 
    IconData icon, 
    String label, 
    String value, 
    Color color
  ) {
    return Expanded(
      child: Card(
        elevation: 2,
        child: Padding(
          padding: EdgeInsets.all(16),
          child: Column(
            children: [
              Icon(icon, color: color),
              SizedBox(height: 8),
              Text(
                label,
                style: TextStyle(color: Colors.grey.shade700),
              ),
              SizedBox(height: 4),
              Text(
                value,
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 18,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
  
  Widget _buildNoImagesMessage(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.no_photography, size: 64, color: Colors.grey),
          SizedBox(height: 16),
          Text(
            'No images selected',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
          SizedBox(height: 8),
          Text(
            'You didn\'t select any generated images during this session.',
            textAlign: TextAlign.center,
            style: TextStyle(color: Colors.grey.shade700),
          ),
        ],
      ),
    );
  }
  
  Widget _buildImageTile(BuildContext context, WidgetRef ref, Photo image) {
    return Card(
      elevation: 2,
      clipBehavior: Clip.antiAlias,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Image
          Expanded(
            child: ProgressiveImageWidget(
              photoId: image.id,
              enableAnimation: true,
            ),
          ),
          
          // Controls
          Container(
            color: Colors.grey.shade100,
            padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                IconButton(
                  icon: Icon(Icons.visibility, size: 20),
                  onPressed: () => _showImageDetails(context, ref, image),
                  tooltip: 'View Details',
                  constraints: BoxConstraints(),
                  padding: EdgeInsets.all(4),
                ),
                IconButton(
                  icon: Icon(Icons.share, size: 20),
                  onPressed: () => _shareImage(context, ref, image),
                  tooltip: 'Share',
                  constraints: BoxConstraints(),
                  padding: EdgeInsets.all(4),
                ),
                IconButton(
                  icon: Icon(Icons.delete, size: 20),
                  onPressed: () => _deleteImage(context, ref, image),
                  tooltip: 'Delete',
                  constraints: BoxConstraints(),
                  padding: EdgeInsets.all(4),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
  
  void _showImageDetails(BuildContext context, WidgetRef ref, Photo image) {
    // Implementation to show image details dialog
  }
  
  void _shareImage(BuildContext context, WidgetRef ref, Photo image) {
    // Implementation to share image
  }
  
  void _deleteImage(BuildContext context, WidgetRef ref, Photo image) {
    // Implementation to delete image
  }
  
  void _showCreateAlbumDialog(
    BuildContext context, 
    WidgetRef ref, 
    List<Photo> images
  ) {
    // Implementation to show create album dialog
  }
  
  String _formatDuration(Duration duration) {
    final minutes = duration.inMinutes;
    final seconds = duration.inSeconds % 60;
    
    return '$minutes min $seconds sec';
  }
}
```

### 8. Alert and Notification System
```dart
class NotificationManager extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final notifications = ref.watch(notificationProvider);
    
    if (notifications.isEmpty) {
      return SizedBox.shrink();
    }
    
    return Stack(
      children: [
        // Position the notifications at the bottom of the screen
        Positioned(
          bottom: 16,
          right: 16,
          width: 300,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              for (final notification in notifications)
                NotificationCard(
                  notification: notification,
                  onDismiss: () => ref.read(notificationProvider.notifier).dismiss(notification.id),
                ),
            ],
          ),
        ),
      ],
    );
  }
}

class NotificationCard extends StatefulWidget {
  final AppNotification notification;
  final VoidCallback onDismiss;
  
  const NotificationCard({
    Key? key,
    required this.notification,
    required this.onDismiss,
  }) : super(key: key);
  
  @override
  _NotificationCardState createState() => _NotificationCardState();
}

class _NotificationCardState extends State<NotificationCard> with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _fadeAnimation;
  late Animation<Offset> _slideAnimation;
  
  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: Duration(milliseconds: 300),
      vsync: this,
    );
    
    _fadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(CurvedAnimation(
      parent: _controller,
      curve: Curves.easeOut,
    ));
    
    _slideAnimation = Tween<Offset>(
      begin: Offset(1.0, 0.0),
      end: Offset.zero,
    ).animate(CurvedAnimation(
      parent: _controller,
      curve: Curves.easeOut,
    ));
    
    _controller.forward();
    
    // Auto-dismiss after duration if specified
    if (widget.notification.autoDismissDuration != null) {
      Future.delayed(widget.notification.autoDismissDuration!, () {
        if (mounted) {
          _dismiss();
        }
      });
    }
  }
  
  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }
  
  void _dismiss() {
    _controller.reverse().then((_) {
      widget.onDismiss();
    });
  }
  
  @override
  Widget build(BuildContext context) {
    return SlideTransition(
      position: _slideAnimation,
      child: FadeTransition(
        opacity: _fadeAnimation,
        child: Card(
          elevation: 4,
          margin: EdgeInsets.only(bottom: 8),
          color: _getNotificationColor(widget.notification.type),
          child: ListTile(
            leading: Icon(
              _getNotificationIcon(widget.notification.type),
              color: Colors.white,
            ),
            title: Text(
              widget.notification.title,
              style: TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.bold,
              ),
            ),
            subtitle: widget.notification.message != null
                ? Text(
                    widget.notification.message!,
                    style: TextStyle(color: Colors.white.withOpacity(0.9)),
                  )
                : null,
            trailing: IconButton(
              icon: Icon(Icons.close, color: Colors.white),
              onPressed: _dismiss,
            ),
            onTap: widget.notification.onTap,
          ),
        ),
      ),
    );
  }
  
  Color _getNotificationColor(NotificationType type) {
    switch (type) {
      case NotificationType.success:
        return Colors.green;
      case NotificationType.info:
        return Colors.blue;
      case NotificationType.warning:
        return Colors.orange;
      case NotificationType.error:
        return Colors.red;
    }
  }
  
  IconData _getNotificationIcon(NotificationType type) {
    switch (type) {
      case NotificationType.success:
        return Icons.check_circle;
      case NotificationType.info:
        return Icons.info;
      case NotificationType.warning:
        return Icons.warning;
      case NotificationType.error:
        return Icons.error;
    }
  }
}

// Notification models and providers
enum NotificationType {
  success,
  info,
  warning,
  error
}

class AppNotification {
  final String id;
  final String title;
  final String? message;
  final NotificationType type;
  final Duration? autoDismissDuration;
  final VoidCallback? onTap;
  
  AppNotification({
    required this.title,
    this.message,
    required this.type,
    this.autoDismissDuration = const Duration(seconds: 5),
    this.onTap,
  }) : id = uuid.v4();
}

class NotificationService extends StateNotifier<List<AppNotification>> {
  NotificationService() : super([]);
  
  void show({
    required String title,
    String? message,
    required NotificationType type,
    Duration? autoDismissDuration,
    VoidCallback? onTap,
  }) {
    final notification = AppNotification(
      title: title,
      message: message,
      type: type,
      autoDismissDuration: autoDismissDuration,
      onTap: onTap,
    );
    
    state = [...state, notification];
  }
  
  void showSuccess(String title, {String? message, VoidCallback? onTap}) {
    show(
      title: title,
      message: message,
      type: NotificationType.success,
      onTap: onTap,
    );
  }
  
  void showInfo(String title, {String? message, VoidCallback? onTap}) {
    show(
      title: title,
      message: message,
      type: NotificationType.info,
      onTap: onTap,
    );
  }
  
  void showWarning(String title, {String? message, VoidCallback? onTap}) {
    show(
      title: title,
      message: message,
      type: NotificationType.warning,
      onTap: onTap,
    );
  }
  
  void showError(String title, {String? message, VoidCallback? onTap}) {
    show(
      title: title,
      message: message,
      type: NotificationType.error,
      autoDismissDuration: null, // Errors don't auto-dismiss
      onTap: onTap,
    );
  }
  
  void dismiss(String id) {
    state = state.where((notification) => notification.id != id).toList();
  }
  
  void dismissAll() {
    state = [];
  }
}

final notificationProvider = StateNotifierProvider<NotificationService, List<AppNotification>>((ref) {
  return NotificationService();
});
```

### 9. Settings Interface
```dart
class BackendSettingsInterface extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final settings = ref.watch(settingsProvider);
    final isEditing = ref.watch(isEditingSettingsProvider);
    
    return Card(
      margin: EdgeInsets.all(16),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.settings, color: Colors.grey.shade700),
                SizedBox(width: 8),
                Text(
                  'Backend Settings',
                  style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                Spacer(),
                TextButton(
                  onPressed: () => ref.read(isEditingSettingsProvider.notifier).state = !isEditing,
                  child: Text(isEditing ? 'Cancel' : 'Edit'),
                ),
              ],
            ),
            
            Divider(),
            
            // Connection settings
            _buildConnectionSettings(context, ref, settings, isEditing),
            
            Divider(),
            
            // Generation defaults
            _buildGenerationDefaults(context, ref, settings, isEditing),
            
            Divider(),
            
            // Remote backend settings
            if (settings.useRemoteBackend || isEditing)
              _buildRemoteSettings(context, ref, settings, isEditing),
            
            if (isEditing) ...[
              Divider(),
              
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  ElevatedButton(
                    onPressed: () => _saveSettings(context, ref),
                    child: Text('Save Changes'),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }
  
  Widget _buildConnectionSettings(
    BuildContext context, 
    WidgetRef ref, 
    AppSettings settings, 
    bool isEditing
  ) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Connection',
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
        SizedBox(height: 16),
        
        // Backend mode
        ListTile(
          contentPadding: EdgeInsets.zero,
          title: Text('Backend Mode'),
          subtitle: Text(settings.useRemoteBackend ? 'Remote' : 'Local'),
          trailing: isEditing
              ? Switch(
                  value: settings.useRemoteBackend,
                  onChanged: (value) => ref.read(settingsProvider.notifier).updateUseRemote(value),
                )
              : null,
        ),
        
        // Local URL
        if (!settings.useRemoteBackend || isEditing)
          isEditing
              ? TextFormField(
                  decoration: InputDecoration(
                    labelText: 'Local InvokeAI URL',
                    hintText: 'http://localhost:9090',
                  ),
                  initialValue: settings.localBackendUrl,
                  onChanged: (value) => ref.read(settingsProvider.notifier).updateLocalUrl(value),
                )
              : ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: Text('Local InvokeAI URL'),
                  subtitle: Text(settings.localBackendUrl),
                ),
        
        SizedBox(height: 8),
        
        // Connection test button
        OutlinedButton.icon(
          icon: Icon(Icons.link),
          label: Text('Test Connection'),
          onPressed: () => _testConnection(context, ref),
        ),
      ],
    );
  }
  
  Widget _buildGenerationDefaults(
    BuildContext context, 
    WidgetRef ref, 
    AppSettings settings, 
    bool isEditing
  ) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Generation Defaults',
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),# Updated Frontend Implementation Guide

## Core Architecture

### State Management
- Riverpod as primary state management solution
- Strict unidirectional data flow
- Clear separation between UI and business logic
- Support for both local and remote InvokeAI instances

```dart
// Core providers
final photoRepositoryProvider = Provider<PhotoRepository>((ref) => PhotoRepository());
final photoCacheProvider = Provider<PhotoCacheService>((ref) => PhotoCacheService());
final invokeAIClientProvider = Provider<InvokeAIClient>((ref) => InvokeAIClient());
final backendManagerProvider = Provider<BackendManager>((ref) => BackendManager());
final modelCacheProvider = Provider<ModelCacheService>((ref) => ModelCacheService());

// Generation workflow providers
final generationSessionProvider = StateNotifierProvider<GenerationSessionNotifier, GenerationSessionState>((ref) {
  return GenerationSessionNotifier(
    ref.watch(invokeAIClientProvider),
    ref.watch(photoRepositoryProvider),
    ref.watch(modelCacheProvider),
  );
}

## Additional Required Components

The following components will also need to be implemented to complete the frontend:

### 1. Session History View
```dart
class SessionHistoryView extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final sessionsAsync = ref.watch(sessionHistoryProvider);
    
    return sessionsAsync.when(
      data: (sessions) => _buildSessionsList(context, ref, sessions),
      loading: () => Center(child: CircularProgressIndicator()),
      error: (error, _) => Center(
        child: Text('Error loading sessions: $error'),
      ),
    );
  }
  
  Widget _buildSessionsList(
    BuildContext context, 
    WidgetRef ref, 
    List<GenerationSession> sessions
  ) {
    if (sessions.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.history, size: 64, color: Colors.grey),
            SizedBox(height: 16),
            Text(
              'No generation sessions yet',
              style: Theme.of(context).textTheme.headline6,
            ),
            SizedBox(height: 8),
            Text(
              'Your generation sessions will appear here',
              style: TextStyle(color: Colors.grey.shade600),
            ),
            SizedBox(height: 24),
            ElevatedButton.icon(
              icon: Icon(Icons.add),
              label: Text('Start a New Session'),
              onPressed: () => ref.read(generationSessionProvider.notifier)
                  .createSession('scratch', null),
            ),
          ],
        ),
      );
    }
    
    return ListView.builder(
      itemCount: sessions.length,
      itemBuilder: (context, index) {
        final session = sessions[index];
        return SessionHistoryCard(session: session);
      },
    );
  }
}

class SessionHistoryCard extends ConsumerWidget {
  final GenerationSession session;
  
  const SessionHistoryCard({Key? key, required this.session}) : super(key: key);
  
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Card(
      margin: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: InkWell(
        onTap: () => ref.read(generationSessionProvider.notifier)
            .loadSession(session.id),
        child: Padding(
          padding: EdgeInsets.all(16),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Thumbnail or icon
              if (session.latestImageId != null)
                ClipRRect(
                  borderRadius: BorderRadius.circular(8),
                  child: SizedBox(
                    width: 80,
                    height: 80,
                    child: ProgressiveImageWidget(
                      photoId: session.latestImageId!,
                      enableAnimation: false,
                    ),
                  ),
                )
              else
                Container(
                  width: 80,
                  height: 80,
                  decoration: BoxDecoration(
                    color: Colors.grey.shade200,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Icon(
                    Icons.image_not_supported_outlined, 
                    color: Colors.grey.shade400,
                    size: 32,
                  ),
                ),
              
              SizedBox(width: 16),
              
              // Session info
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      _formatSessionTitle(session),
                      style: Theme.of(context).textTheme.subtitle1!.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    SizedBox(height: 4),
                    Text(
                      'Created: ${_formatDateTime(session.started_at)}',
                      style: TextStyle(color: Colors.grey.shade700),
                    ),
                    SizedBox(height: 4),
                    Text(
                      '${session.steps_count} steps · ${session.total_images_generated} images',
                    ),
                    SizedBox(height: 8),
                    _buildStatusChip(context, session.status),
                  ],
                ),
              ),
              
              // Navigation icon
              Icon(Icons.chevron_right),
            ],
          ),
        ),
      ),
    );
  }
  
  Widget _buildStatusChip(BuildContext context, String status) {
    Color chipColor;
    String label;
    
    switch (status) {
      case 'active':
        chipColor = Colors.blue;
        label = 'Active';
        break;
      case 'completed':
        chipColor = Colors.green;
        label = 'Completed';
        break;
      case 'abandoned':
        chipColor = Colors.orange;
        label = 'Abandoned';
        break;
      default:
        chipColor = Colors.grey;
        label = status;
    }
    
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: chipColor.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: chipColor.withOpacity(0.3)),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: chipColor,
          fontSize: 12,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }
  
  String _formatSessionTitle(GenerationSession session) {
    final date = session.started_at.toLocal();
    final formattedDate = '${date.month}/${date.day}/${date.year}';
    final formattedTime = '${date.hour}:${date.minute.toString().padLeft(2, '0')}';
    
    return 'Session on $formattedDate at $formattedTime';
  }
  
  String _formatDateTime(DateTime dateTime) {
    final now = DateTime.now();
    final difference = now.difference(dateTime);
    
    if (difference.inDays < 1) {
      if (difference.inHours < 1) {
        if (difference.inMinutes < 1) {
          return 'Just now';
        }
        return '${difference.inMinutes} minute${difference.inMinutes > 1 ? 's' : ''} ago';
      }
      return '${difference.inHours} hour${difference.inHours > 1 ? 's' : ''} ago';
    } else if (difference.inDays < 7) {
      return '${difference.inDays} day${difference.inDays > 1 ? 's' : ''} ago';
    } else {
      final date = dateTime.toLocal();
      return '${date.month}/${date.day}/${date.year}';
    }
  }
}
```

### 2. Timeline Navigation Component
```dart
class TimelineNavigationComponent extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final sessionState = ref.watch(generationSessionProvider);
    
    if (sessionState.steps.isEmpty) {
      return SizedBox.shrink();
    }
    
    return Container(
      height: 150,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Text(
              'Generation Timeline',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
          ),
          
          Expanded(
            child: _buildTimelineList(context, ref, sessionState),
          ),
        ],
      ),
    );
  }
  
  Widget _buildTimelineList(
    BuildContext context, 
    WidgetRef ref, 
    GenerationSessionState state
  ) {
    final currentStepId = state.currentStep?.id;
    
    return ListView.builder(
      scrollDirection: Axis.horizontal,
      padding: EdgeInsets.symmetric(horizontal: 16),
      itemCount: state.steps.length,
      itemBuilder: (context, index) {
        final step = state.steps[index];
        final isSelected = step.id == currentStepId;
        
        return _TimelineItem(
          step: step,
          position: index + 1,
          isSelected: isSelected,
          onTap: () => ref.read(generationStepProvider.notifier).selectStep(step.id),
        );
      },
    );
  }
}

class _TimelineItem extends StatelessWidget {
  final GenerationStep step;
  final int position;
  final bool isSelected;
  final VoidCallback onTap;
  
  const _TimelineItem({
    Key? key,
    required this.step,
    required this.position,
    required this.isSelected,
    required this.onTap,
  }) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 100,
        margin: EdgeInsets.symmetric(horizontal: 4),
        decoration: BoxDecoration(
          border: Border.all(
            color: isSelected
                ? Theme.of(context).primaryColor
                : Colors.grey.shade300,
            width: isSelected ? 2 : 1,
          ),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Column(
          children: [
            // Step number indicator
            Container(
              width: double.infinity,
              padding: EdgeInsets.symmetric(vertical: 4),
              decoration: BoxDecoration(
                color: isSelected
                    ? Theme.of(context).primaryColor
                    : Colors.grey.shade200,
                borderRadius: BorderRadius.vertical(top: Radius.circular(6)),
              ),
              child: Text(
                'Step $position',
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  color: isSelected ? Colors.white : Colors.black,
                  fontSize: 12,
                ),
                textAlign: TextAlign.center,
              ),
            ),
            
            // Image preview
            Expanded(
              child: step.selected_image_id != null
                  ? ProgressiveImageWidget(
                      photoId: step.selected_image_id!,
                      enableAnimation: false,
                    )
                  : Center(
                      child: Icon(
                        Icons.hourglass_empty,
                        color: Colors.grey,
                      ),
                    ),
            ),
            
            // Step status indicator
            Container(
              width: double.infinity,
              padding: EdgeInsets.symmetric(vertical: 2),
              color: _getStatusColor(step.status).withOpacity(0.1),
              child: Text(
                _getStatusText(step.status),
                style: TextStyle(
                  fontSize: 10,
                  color: _getStatusColor(step.status),
                ),
                textAlign: TextAlign.center,
              ),
            ),
          ],
        ),
      ),
    );
  }
  
  Color _getStatusColor(String status) {
    switch (status) {
      case 'pending':
        return Colors.orange;
      case 'processing':
        return Colors.blue;
      case 'completed':
        return Colors.green;
      case 'failed':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }
  
  String _getStatusText(String status) {
    switch (status) {
      case 'pending':
        return 'Pending';
      case 'processing':
        return 'Processing';
      case 'completed':
        return 'Completed';
      case 'failed':
        return 'Failed';
      default:
        return status;
    }
  }
}
```

### 3. Image Comparison Tool
```dart
class ImageComparisonTool extends ConsumerWidget {
  final String originalImageId;
  final String generatedImageId;
  
  const ImageComparisonTool({
    Key? key,
    required this.originalImageId,
    required this.generatedImageId,
  }) : super(key: key);
  
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final comparisonMode = ref.watch(comparisonModeProvider);
    
    return Column(
      children: [
        // Comparison mode selector
        Padding(
          padding: EdgeInsets.all(16),
          child: SegmentedButton<ComparisonMode>(
            segments: [
              ButtonSegment(
                value: ComparisonMode.sideBySide,
                label: Text('Side by Side'),
                icon: Icon(Icons.view_agenda),
              ),
              ButtonSegment(
                value: ComparisonMode.slider,
                label: Text('Slider'),
                icon: Icon(Icons.compare),
              ),
              ButtonSegment(
                value: ComparisonMode.overlay,
                label: Text('Overlay'),
                icon: Icon(Icons.layers),
              ),
            ],
            selected: {comparisonMode},
            onSelectionChanged: (newSelection) {
              if (newSelection.isNotEmpty) {
                ref.read(comparisonModeProvider.notifier).state = newSelection.first;
              }
            },
          ),
        ),
        
        // Comparison view
        Expanded(
          child: Padding(
            padding: EdgeInsets.all(16),
            child: _buildComparisonView(context, comparisonMode),
          ),
        ),
        
        // Image metadata comparison
        _buildMetadataComparison(context, ref),
      ],
    );
  }
  
  Widget _buildComparisonView(BuildContext context, ComparisonMode mode) {
    switch (mode) {
      case ComparisonMode.sideBySide:
        return Row(
          children: [
            Expanded(
              child: Column(
                children: [
                  Text('Original', style: TextStyle(fontWeight: FontWeight.bold)),
                  SizedBox(height: 8),
                  Expanded(
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(8),
                      child: ProgressiveImageWidget(
                        photoId: originalImageId,
                        enableAnimation: false,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            SizedBox(width: 16),
            Expanded(
              child: Column(
                children: [
                  Text('Generated', style: TextStyle(fontWeight: FontWeight.bold)),
                  SizedBox(height: 8),
                  Expanded(
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(8),
                      child: ProgressiveImageWidget(
                        photoId: generatedImageId,
                        enableAnimation: false,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        );
        
      case ComparisonMode.slider:
        return ImageCompareSlider(
          itemOne: ProgressiveImageWidget(
            photoId: originalImageId,
            enableAnimation: false,
          ),
          itemTwo: ProgressiveImageWidget(
            photoId: generatedImageId,
            enableAnimation: false,
          ),
          dividerWidth: 2,
          dividerColor: Theme.of(context).primaryColor,
          handleSize: Size(40, 40),
          handleLabelBuilder: (position) => position == 0 ? "Original" : "Generated",
        );
        
      case ComparisonMode.overlay:
        return Stack(
          children: [
            // Base layer
            Positioned.fill(
              child: ProgressiveImageWidget(
                photoId: originalImageId,
                enableAnimation: false,
              ),
            ),
            
            // Overlay layer with opacity slider
            Positioned.fill(
              child: Opacity(
                opacity: 0.7, // This could be controlled by a slider
                child: ProgressiveImageWidget(
                  photoId: generatedImageId,
                  enableAnimation: false,
                ),
              ),
            ),
            
            // Labels
            Positioned(
              left: 16,
              top: 16,
              child: Container(
                padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.black.withOpacity(0.6),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  'Original + Generated',
                  style: TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ),
          ],
        );
    }
  }
  
  Widget _buildMetadataComparison(BuildContext context, WidgetRef ref) {
    final originalPhotoAsync = ref.watch(photoProvider(originalImageId));
    final generatedPhotoAsync = ref.watch(photoProvider(generatedImageId));
    
    // This is a simplified version - would need to be expanded
    // with actual metadata comparison
    return Card(
      margin: EdgeInsets.all(16),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Generation Parameters', style: TextStyle(fontWeight: FontWeight.bold)),
            SizedBox(height: 8),
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Original', style: TextStyle(fontWeight: FontWeight.w500)),
                      SizedBox(height: 4),
                      Text('Dimensions: ${generatedPhotoAsync.width}x${generatedPhotoAsync.height}'),
                      if (!generatedPhotoAsync.is_generated)
                        Text('User upload (not generated)'),
                    ],
                  ),
                ),
                SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Generated', style: TextStyle(fontWeight: FontWeight.w500)),
                      SizedBox(height: 4),
                      Text('Prompt: ${generatedPhotoAsync.generation_prompt ?? "N/A"}'),
                      Text('Model: ${generatedPhotoAsync.model_name ?? "N/A"}'),
                      Text('Seed: ${generatedPhotoAsync.seed ?? "N/A"}'),
                    ],
                  ),
                ),
              ],
            ),
          ],
        );

final generationStepProvider = StateNotifierProvider<GenerationStepNotifier, GenerationStepState>((ref) {
  return GenerationStepNotifier(
    ref.watch(invokeAIClientProvider),
    ref.watch(photoRepositoryProvider),
    ref.watch(modelCacheProvider),
  );
});

// Model management provider
final modelsProvider = FutureProvider<List<Model>>((ref) {
  final client = ref.watch(invokeAIClientProvider);
  final modelCache = ref.watch(modelCacheProvider);
  
  // First check cache, then refresh if needed
  if (modelCache.hasValidCache()) {
    return modelCache.getAllModels();
  }
  
  return client.getModels(refresh: true);
});

// Remote backend state
final backendStatusProvider = StateNotifierProvider<BackendStatusNotifier, BackendStatus>((ref) {
  return BackendStatusNotifier(
    ref.watch(backendManagerProvider),
    ref.watch(settingsProvider),
  );
});

// Retrieval status provider
final retrievalStatusProvider = Provider.family<RetrievalStatus, String>((ref, stepId) {
  final step = ref.watch(generationStepProvider).currentStep;
  if (step?.id != stepId) return RetrievalStatus.unknown;
  
  return RetrievalStatus(
    total: step?.batchSize ?? 0,
    completed: step?.imagesRetrieved ?? 0,
    pending: step?.imagesPending ?? 0,
    failed: step?.imagesFailed ?? 0
  );
});

// State classes
class BackendStatus {
  final bool isRemote;
  final bool isConnected;
  final String baseUrl;
  final String? apiVersion;
  final String? podId;
  final String? podStatus;
  final DateTime? lastActivity;
  final Duration? uptime;
  final double? currentCost;
  
  const BackendStatus({
    required this.isRemote,
    required this.isConnected,
    required this.baseUrl,
    this.apiVersion,
    this.podId,
    this.podStatus,
    this.lastActivity,
    this.uptime,
    this.currentCost,
  });
}

class GenerationSessionState {
  final GenerationSession? currentSession;
  final List<GenerationStep> steps;
  final bool isLoading;
  final String? error;
  final String correlationId; // Used for tracking image retrieval
  
  const GenerationSessionState({
    this.currentSession,
    this.steps = const [],
    this.isLoading = false,
    this.error,
    this.correlationId = '', // Will be generated on session creation
  });
}

class GenerationStepState {
  final GenerationStep? currentStep;
  final List<StepAlternative> alternatives;
  final bool isLoading;
  final String? error;
  final RetrievalStatus retrievalStatus;
  
  const GenerationStepState({
    this.currentStep,
    this.alternatives = const [],
    this.isLoading = false,
    this.error,
    this.retrievalStatus = const RetrievalStatus(),
  });
}

class Model {
  final String id; // Usually a UUID
  final String key; // UUID key required by InvokeAI
  final String hash; // Blake3 hash required by InvokeAI
  final String name;
  final String type; // main, vae, etc.
  final String base; // sdxl, sd15, etc.
  final List<VaeModel> compatibleVaes;
  final GenerationDefaults defaults;
  
  // Constructor
  Model({
    required this.id,
    required this.key,
    required this.hash,
    required this.name,
    required this.type,
    required this.base,
    this.compatibleVaes = const [],
    required this.defaults,
  });
}

class RetrievalStatus {
  final int total;
  final int completed;
  final int pending;
  final int failed;
  
  const RetrievalStatus({
    this.total = 0,
    this.completed = 0,
    this.pending = 0,
    this.failed = 0,
  });
  
  bool get isComplete => total > 0 && completed == total;
  bool get hasFailures => failed > 0;
  double get progressPercentage => total > 0 ? (completed / total) * 100 : 0;
}
```

### Cache Strategy

#### Extended Two-Tier Caching
1. Memory Cache (LRU)
   - Recent photos for quick access
   - Configurable size limit
   - Eviction on memory pressure

2. Disk Cache
   - All downloaded photos
   - Thumbnails
   - Support for offline viewing
   - Session-based organization

```dart
class PhotoCacheService {
  static const int _memoryCacheSize = 100; // Number of photos
  static const int _diskCacheSize = 500 * 1024 * 1024; // 500MB
  
  final LRUMap<String, Uint8List> _memoryCache;
  final PhotoCacheManager _diskCache;
  
  PhotoCacheService() : 
    _memoryCache = LRUMap(maximumSize: _memoryCacheSize),
    _diskCache = PhotoCacheManager(maxCacheSize: _diskCacheSize);

  Future<Uint8List?> getPhoto(String id, {bool thumbnail = false}) async {
    // Check memory cache first
    final key = thumbnail ? '$id.thumb' : id;
    if (_memoryCache.containsKey(key)) {
      return _memoryCache[key];
    }
    
    // Check disk cache
    final data = await _diskCache.get<Uint8List>(key);
    if (data != null) {
      _memoryCache[key] = data;
    }
    return data;
  }
  
  // Cache photos specifically for current generation session
  Future<void> cacheSessionPhotos(String sessionId) async {
    // Implementation to prioritize caching of session-related images
  }
}

// Model Cache Service
class ModelCacheService {
  static const Duration _cacheTtl = Duration(minutes: 15);
  
  final Map<String, Model> _modelCache = {};
  DateTime? _lastCacheUpdate;
  
  bool hasValidCache() {
    if (_lastCacheUpdate == null) return false;
    return DateTime.now().difference(_lastCacheUpdate!) < _cacheTtl;
  }
  
  void updateModels(List<Model> models) {
    _modelCache.clear();
    for (final model in models) {
      _modelCache[model.key] = model;
    }
    _lastCacheUpdate = DateTime.now();
  }
  
  List<Model> getAllModels() {
    return _modelCache.values.toList();
  }
  
  Model? getModelByKey(String key) {
    return _modelCache[key];
  }
  
  List<Model> getModelsByType(String type) {
    return _modelCache.values.where((model) => model.type == type).toList();
  }
  
  VaeModel? getDefaultVaeForModel(String modelKey) {
    final model = _modelCache[modelKey];
    if (model == null) return null;
    
    final compatibleVaes = model.compatibleVaes;
    if (compatibleVaes.isEmpty) return null;
    
    // Find the default VAE (usually marked as default or with 'fp16' in the name)
    final defaultVae = compatibleVaes.firstWhere(
      (vae) => vae.isDefault,
      orElse: () => compatibleVaes.first
    );
    
    return defaultVae;
  }
}
```

### Image Loading & Display

#### Progressive Loading Implementation with Retrieval Status
```dart
class ProgressiveImageWidget extends StatelessWidget {
  final String photoId;
  final bool enableAnimation;
  final Function()? onRetryPressed;

  const ProgressiveImageWidget({
    Key? key, 
    required this.photoId, 
    this.enableAnimation = true,
    this.onRetryPressed,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Consumer(builder: (context, ref, _) {
      final photo = ref.watch(photoProvider(photoId));
      
      // Handle retrieval status
      if (photo.retrieval_status == 'pending' || photo.retrieval_status == 'processing') {
        return Stack(
          children: [
            // Placeholder or low-res preview
            Container(
              color: Colors.grey.shade200,
              child: Center(
                child: CircularProgressIndicator(),
              ),
            ),
            
            // Status indicator
            Positioned(
              bottom: 8,
              right: 8,
              child: _buildStatusIndicator(photo.retrieval_status),
            ),
          ],
        );
      } else if (photo.retrieval_status == 'failed') {
        return Stack(
          children: [
            // Error placeholder
            Container(
              color: Colors.grey.shade200,
              child: Center(
                child: IconButton(
                  icon: Icon(Icons.refresh),
                  onPressed: onRetryPressed ?? () => 
                    ref.read(photoRepositoryProvider).retryRetrieval(photoId),
                ),
              ),
            ),
            
            // Status indicator
            Positioned(
              bottom: 8,
              right: 8,
              child: _buildStatusIndicator(photo.retrieval_status),
            ),
          ],
        );
      }
      
      // Normal progressive loading for completed retrievals
      return Stack(
        children: [
          // Blurred thumbnail
          CachedThumbnailImage(
            photoId: photoId,
            fit: BoxFit.cover,
            imageBuilder: (context, imageProvider) => ImageFiltered(
              imageFilter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
              child: Image(image: imageProvider),
            ),
          ),
          
          // Full resolution image with fade-in
          CachedNetworkImage(
            photoId: photoId,
            fadeInDuration: enableAnimation ? Duration(milliseconds: 300) : Duration.zero,
            placeholder: (context, url) => Container(),
          ),
        ],
      );
    });
  }
  
  Widget _buildStatusIndicator(String status) {
    switch (status) {
      case 'pending':
        return Container(
          padding: EdgeInsets.all(4),
          decoration: BoxDecoration(
            color: Colors.orange.withOpacity(0.8),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Icon(Icons.hourglass_empty, size: 16, color: Colors.white),
        );
      case 'processing':
        return Container(
          padding: EdgeInsets.all(4),
          decoration: BoxDecoration(
            color: Colors.blue.withOpacity(0.8),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Icon(Icons.sync, size: 16, color: Colors.white),
        );
      case 'failed':
        return Container(
          padding: EdgeInsets.all(4),
          decoration: BoxDecoration(
            color: Colors.red.withOpacity(0.8),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Icon(Icons.error_outline, size: 16, color: Colors.white),
        );
      default:
        return Container(); // No indicator for completed
    }
  }
}
```

### Backend Connection Management

```dart
class BackendManager {
  final HttpClient _client;
  final SettingsService _settings;
  
  BackendManager(this._client, this._settings);
  
  Future<BackendStatus> getStatus() async {
    try {
      final isRemote = _settings.useRemoteBackend;
      final baseUrl = isRemote ? _settings.remoteBackendUrl : 'http://localhost:9090';
      
      final response = await _client.get('$baseUrl/api/v1/app/version');
      if (response.statusCode == 200) {
        // Backend is connected, extract version info
        final data = jsonDecode(response.body);
        final apiVersion = data['version'] as String?;
        
        // Get additional info for remote backends
        if (isRemote) {
          final podStatus = await _getPodStatus();
          return BackendStatus(
            isRemote: true,
            isConnected: true,
            baseUrl: baseUrl,
            apiVersion: apiVersion,
            podId: podStatus['pod_id'],
            podStatus: podStatus['status'],
            lastActivity: DateTime.parse(podStatus['last_activity']),
            uptime: Duration(seconds: podStatus['uptime']),
            currentCost: podStatus['current_cost'],
          );
        } else {
          return BackendStatus(
            isRemote: false,
            isConnected: true,
            baseUrl: baseUrl,
            apiVersion: apiVersion,
          );
        }
      } else {
        return BackendStatus(
          isRemote: isRemote,
          isConnected: false,
          baseUrl: baseUrl,
        );
      }
    } catch (e) {
      return BackendStatus(
        isRemote: _settings.useRemoteBackend,
        isConnected: false,
        baseUrl: _settings.useRemoteBackend ? _settings.remoteBackendUrl : 'http://localhost:9090',
        error: e.toString(),
      );
    }
  }
  
  Future<Map<String, dynamic>> _getPodStatus() async {
    // Implementation to get pod status
    // ...
  }
  
  Future<bool> switchMode(bool useRemote) async {
    try {
      // 1. Update settings
      await _settings.setUseRemoteBackend(useRemote);
      
      // 2. If switching to remote mode, ensure pod is running
      if (useRemote) {
        final podStatus = await _getPodStatus();
        if (podStatus['status'] != 'running') {
          await startPod();
        }
      }
      
      // 3. Test connection with new mode
      final status = await getStatus();
      return status.isConnected;
    } catch (e) {
      print(f"Error switching modes: {e}");
      return false;
    }
  }
  
  Future<Map<String, dynamic>> startPod() async {
    // Implementation to start remote pod
    // ...
  }
  
  Future<bool> stopPod() async {
    // Implementation to stop remote pod
    // ...
  }
  
  // New method to handle model retrieval with caching
  Future<List<Model>> getModels({bool refresh = false}) async {
    final status = await getStatus();
    if (!status.isConnected) {
      throw ConnectionError('Cannot connect to InvokeAI backend');
    }
    
    // Model caching logic is now implemented in ModelCacheService
    // This method is just a facade to the InvokeAI API
    
    try {
      final response = await _client.get('${status.baseUrl}/api/v2/models/');
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final models = <Model>[];
        
        // Process models from response
        for (final modelData in data['models']) {
          if (modelData['type'] == 'main') {
            // Find compatible VAEs for this model
            final base = modelData['base'];
            final compatibleVaes = data['models']
                .where((m) => m['type'] == 'vae' && m['base'] == base)
                .map((m) => VaeModel.fromJson(m))
                .toList();
            
            models.add(Model(
              id: modelData['key'],
              key: modelData['key'],
              hash: modelData['hash'],
              name: modelData['name'],
              type: modelData['type'],
              base: modelData['base'],
              compatibleVaes: compatibleVaes,
              defaults: GenerationDefaults.fromJson(modelData['default_settings'] ?? {}),
            ));
          }
        }
        
        return models;
      } else {
        throw ApiError('Failed to get models: ${response.statusCode}');
      }
    } catch (e) {
      throw ApiError('Error getting models: $e');
    }
  }
}

class VaeModel {
  final String key;
  final String hash;
  final String name;
  final bool isDefault;
  
  VaeModel({
    required this.key,
    required this.hash,
    required this.name,
    this.isDefault = false,
  });
  
  factory VaeModel.fromJson(Map<String, dynamic> json) {
    return VaeModel(
      key: json['key'],
      hash: json['hash'],
      name: json['name'],
      isDefault: json['is_default'] ?? false,
    );
  }
}

class GenerationDefaults {
  final int width;
  final int height;
  final int steps;
  final double cfgScale;
  final String scheduler;
  
  GenerationDefaults({
    this.width = 1024,
    this.height = 1024,
    this.steps = 30,
    this.cfgScale = 7.5,
    this.scheduler = 'euler',
  });
  
  factory GenerationDefaults.fromJson(Map<String, dynamic> json) {
    return GenerationDefaults(
      width: json['width'] ?? 1024,
      height: json['height'] ?? 1024,
      steps: json['steps'] ?? 30,
      cfgScale: (json['cfg_scale'] ?? 7.5).toDouble(),
      scheduler: json['scheduler'] ?? 'euler',
    );
  }
}
```

## Generation Workflow UI Components

### Model Selection Interface

```dart
class ModelSelectionWidget extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final modelsAsync = ref.watch(modelsProvider);
    
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: modelsAsync.when(
          data: (models) => _buildModelSelector(context, ref, models),
          loading: () => Center(child: CircularProgressIndicator()),
          error: (error, stack) => _buildErrorWidget(context, error),
        ),
      ),
    );
  }
  
  Widget _buildModelSelector(BuildContext context, WidgetRef ref, List<Model> models) {
    final selectedModelKey = ref.watch(selectedModelProvider).modelKey;
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Select Model',
          style: Theme.of(context).textTheme.headline6,
        ),
        
        SizedBox(height: 8),
        
        // Model selection grid
        GridView.builder(
          shrinkWrap: true,
          physics: NeverScrollableScrollPhysics(),
          gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: 2,
            crossAxisSpacing: 8,
            mainAxisSpacing: 8,
            childAspectRatio: 3,
          ),
          itemCount: models.length,
          itemBuilder: (context, index) {
            final model = models[index];
            final isSelected = model.key == selectedModelKey;
            
            return InkWell(
              onTap: () => ref.read(selectedModelProvider.notifier)
                  .selectModel(model.key, model.hash),
              child: Container(
                decoration: BoxDecoration(
                  border: Border.all(
                    color: isSelected ? Theme.of(context).primaryColor : Colors.grey.shade300,
                    width: isSelected ? 2 : 1,
                  ),
                  borderRadius: BorderRadius.circular(8),
                ),
                padding: EdgeInsets.all(8),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      model.name,
                      style: TextStyle(
                        fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                      ),
                      overflow: TextOverflow.ellipsis,
                    ),
                    Text(
                      model.base.toUpperCase(),
                      style: TextStyle(
                        fontSize: 12,
                        color: Colors.grey.shade600,
                      ),
                    ),
                  ],
                ),
              ),
            );
          },
        ),
        
        SizedBox(height: 16),
        
        // Selected model details
        if (selectedModelKey != null) _buildSelectedModelDetails(
          context, 
          ref, 
          models.firstWhere((m) => m.key == selectedModelKey)
        ),
        
        // VAE Selection (if applicable)
        if (selectedModelKey != null) _buildVaeSelector(
          context, 
          ref, 
          models.firstWhere((m) => m.key == selectedModelKey)
        ),
      ],
    );
  }
  
  Widget _buildSelectedModelDetails(BuildContext context, WidgetRef ref, Model model) {
    return Container(
      padding: EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.grey.shade100,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Selected Model: ${model.name}',
            style: TextStyle(fontWeight: FontWeight.bold),
          ),
          SizedBox(width: 8),
          Text(
            value,
            style: TextStyle(color: color, fontWeight: FontWeight.w500),
          ),
        ],
      ),
    );
  }
  
  Color _getPodStatusColor(String? status) {
    if (status == null) return Colors.grey;
    
    switch (status.toUpperCase()) {
      case 'RUNNING':
        return Colors.green;
      case 'STARTING':
        return Colors.orange;
      case 'STOPPED':
        return Colors.red;
      case 'ERROR':
        return Colors.red.shade700;
      default:
        return Colors.grey;
    }
  }
  
  String _formatDuration(Duration duration) {
    final hours = duration.inHours;
    final minutes = duration.inMinutes % 60;
    
    if (hours > 0) {
      return '$hours hr ${minutes} min';
    } else {
      return '${minutes} min';
    }
  }
}(height: 4),
          Text('Type: ${model.type} | Base: ${model.base}'),
          Text('Default Resolution: ${model.defaults.width}×${model.defaults.height}'),
          Text('Recommended Steps: ${model.defaults.steps}'),
        ],
      ),
    );
  }
  
  Widget _buildVaeSelector(BuildContext context, WidgetRef ref, Model model) {
    if (model.compatibleVaes.isEmpty) return SizedBox.shrink();
    
    final selectedVaeKey = ref.watch(selectedModelProvider).vaeKey;
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(height: 16),
        Text(
          'VAE Selection',
          style: Theme.of(context).textTheme.subtitle1,
        ),
        SizedBox(height: 8),
        DropdownButtonFormField<String>(
          decoration: InputDecoration(
            labelText: 'VAE Model',
            border: OutlineInputBorder(),
          ),
          value: selectedVaeKey ?? model.compatibleVaes.first.key,
          items: model.compatibleVaes.map((vae) => DropdownMenuItem(
            value: vae.key,
            child: Text(
              vae.name,
              overflow: TextOverflow.ellipsis,
            ),
          )).toList(),
          onChanged: (value) {
            if (value != null) {
              final vae = model.compatibleVaes.firstWhere((v) => v.key == value);
              ref.read(selectedModelProvider.notifier).selectVae(vae.key, vae.hash);
            }
          },
        ),
      ],
    );
  }
  
  Widget _buildErrorWidget(BuildContext context, Object error) {
    return Column(
      children: [
        Icon(Icons.error_outline, color: Colors.red, size: 48),
        SizedBox(height: 16),
        Text('Failed to load models: ${error.toString()}'),
        SizedBox(height: 16),
        ElevatedButton(
          onPressed: () => ref.refresh(modelsProvider),
          child: Text('Retry'),
        ),
      ],
    );
  }
}

// Model selection state
class SelectedModel {
  final String? modelKey;
  final String? modelHash;
  final String? vaeKey;
  final String? vaeHash;
  
  SelectedModel({
    this.modelKey,
    this.modelHash, 
    this.vaeKey,
    this.vaeHash,
  });
  
  SelectedModel copyWith({
    String? modelKey,
    String? modelHash,
    String? vaeKey,
    String? vaeHash,
  }) {
    return SelectedModel(
      modelKey: modelKey ?? this.modelKey,
      modelHash: modelHash ?? this.modelHash,
      vaeKey: vaeKey ?? this.vaeKey,
      vaeHash: vaeHash ?? this.vaeHash,
    );
  }
}

final selectedModelProvider = StateNotifierProvider<SelectedModelNotifier, SelectedModel>((ref) {
  final modelCache = ref.watch(modelCacheProvider);
  return SelectedModelNotifier(modelCache);
});

class SelectedModelNotifier extends StateNotifier<SelectedModel> {
  final ModelCacheService _modelCache;
  
  SelectedModelNotifier(this._modelCache) : super(SelectedModel());
  
  void selectModel(String modelKey, String modelHash) {
    // When selecting a model, also select its default VAE
    final defaultVae = _modelCache.getDefaultVaeForModel(modelKey);
    
    state = state.copyWith(
      modelKey: modelKey,
      modelHash: modelHash,
      vaeKey: defaultVae?.key,
      vaeHash: defaultVae?.hash,
    );
  }
  
  void selectVae(String vaeKey, String vaeHash) {
    state = state.copyWith(
      vaeKey: vaeKey,
      vaeHash: vaeHash,
    );
  }
  
  void reset() {
    state = SelectedModel();
  }
}
```

### Session Manager

```dart
class GenerationSessionManager extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final sessionState = ref.watch(generationSessionProvider);
    
    return Column(
      children: [
        // Session controls
        _buildSessionControls(context, ref, sessionState),
        
        // Steps timeline
        _buildStepsTimeline(context, ref, sessionState),
        
        // Current step editor or alternatives view
        _buildCurrentView(context, ref, sessionState),
      ],
    );
  }
  
  Widget _buildSessionControls(BuildContext context, WidgetRef ref, GenerationSessionState state) {
    return Row(
      children: [
        // Session info
        Text(
          state.currentSession?.id ?? 'No Active Session',
          style: Theme.of(context).textTheme.subtitle1,
        ),
        
        Spacer(),
        
        // Action buttons
        if (state.currentSession != null)
          Row(
            children: [
              OutlinedButton(
                onPressed: () => ref.read(generationSessionProvider.notifier).completeSession(),
                child: Text('Complete'),
              ),
              SizedBox(width: 8),
              OutlinedButton(
                onPressed: () => ref.read(generationSessionProvider.notifier).abandonSession(),
                child: Text('Abandon'),
              ),
            ],
          ),
      ],
    );
  }
  
  Widget _buildStepsTimeline(BuildContext context, WidgetRef ref, GenerationSessionState state) {
    return Container(
      height: 100,
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        itemCount: state.steps.length,
        itemBuilder: (context, index) {
          final step = state.steps[index];
          return GestureDetector(
            onTap: () => ref.read(generationStepProvider.notifier).selectStep(step.id),
            child: Container(
              width: 80,
              margin: EdgeInsets.symmetric(horizontal: 4),
              decoration: BoxDecoration(
                border: Border.all(
                  color: step.id == state.currentStep?.id
                      ? Theme.of(context).primaryColor
                      : Colors.grey.shade300,
                  width: 2,
                ),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Column(
                children: [
                  Expanded(
                    child: step.selected_image_id != null
                        ? ProgressiveImageWidget(photoId: step.selected_image_id!)
                        : Center(child: Text('Step ${index + 1}')),
                  ),
                  Container(
                    padding: EdgeInsets.all(4),
                    color: Theme.of(context).primaryColor.withOpacity(0.1),
                    child: Text(
                      'Step ${index + 1}',
                      style: TextStyle(fontSize: 12),
                      textAlign: TextAlign.center,
                    ),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
  
  Widget _buildCurrentView(BuildContext context, WidgetRef ref, GenerationSessionState state) {
    final stepState = ref.watch(generationStepProvider);
    
    if (stepState.currentStep == null) {
      return StepCreationWidget();
    } else if (stepState.alternatives.isEmpty || stepState.currentStep!.selected_image_id != null) {
      return StepEditorWidget(step: stepState.currentStep!);
    } else {
      return AlternativesGridWidget(
        step: stepState.currentStep!,
        alternatives: stepState.alternatives,
      );
    }
  }
}
```

### Prompt Engineering Editor

```dart
class StepEditorWidget extends ConsumerStatefulWidget {
  final GenerationStep? step;
  
  const StepEditorWidget({Key? key, this.step}) : super(key: key);
  
  @override
  _StepEditorWidgetState createState() => _StepEditorWidgetState();
}

class _StepEditorWidgetState extends ConsumerState<StepEditorWidget> {
  late TextEditingController _promptController;
  late TextEditingController _negativePromptController;
  late Map<String, dynamic> _parameters;
  int _batchSize = 4;
  
  @override
  void initState() {
    super.initState();
    _initializeFromStep();
  }
  
  void _initializeFromStep() {
    final step = widget.step;
    _promptController = TextEditingController(text: step?.prompt ?? '');
    _negativePromptController = TextEditingController(text: step?.negative_prompt ?? '');
    _parameters = Map<String, dynamic>.from(step?.parameters ?? {});
    
    // Get default parameters if starting fresh
    if (step == null) {
      final selectedModel = ref.read(selectedModelProvider);
      if (selectedModel.modelKey != null) {
        final modelCache = ref.read(modelCacheProvider);
        final model = modelCache.getModelByKey(selectedModel.modelKey!);
        if (model != null) {
          _parameters.addAll({
            'width': model.defaults.width,
            'height': model.defaults.height,
            'steps': model.defaults.steps,
            'cfg_scale': model.defaults.cfgScale,
            'scheduler': model.defaults.scheduler,
          });
        } else {
          // Default values if model not found
          _parameters.addAll({
            'width': 1024,
            'height': 1024,
            'steps': 30,
            'cfg_scale': 7.5,
            'scheduler': 'euler',
          });
        }
      }
    }
    
    _batchSize = step?.parameters['batch_size'] ?? 4;
  }
  
  @override
  Widget build(BuildContext context) {
    final selectedModel = ref.watch(selectedModelProvider);
    
    // Check if model is selected
    if (selectedModel.modelKey == null) {
      return _buildModelSelectionRequiredMessage(context);
    }
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        // Prompt editor
        _buildPromptEditor(),
        
        SizedBox(height: 16),
        
        // Generation parameters
        _buildParametersSection(),
        
        SizedBox(height: 16),
        
        // Action buttons
        _buildActionButtons(),
      ],
    );
  }
  
  Widget _buildModelSelectionRequiredMessage(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.model_training, size: 64, color: Colors.grey),
          SizedBox(height: 16),
          Text(
            'Please select a model first',
            style: Theme.of(context).textTheme.headline6,
          ),
          SizedBox(height: 8),
          Text(
            'A model must be selected before creating a generation step.',
            textAlign: TextAlign.center,
          ),
          SizedBox(height: 16),
          ElevatedButton(
            onPressed: () => ref.read(navigationProvider.notifier).navigateTo(NavigationDestination.models),
            child: Text('Select a Model'),
          ),
        ],
      ),
    );
  }
  
  Widget _buildPromptEditor() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Prompt', style: TextStyle(fontWeight: FontWeight.bold)),
        TextField(
          controller: _promptController,
          maxLines: 3,
          decoration: InputDecoration(
            hintText: 'Describe what you want to generate...',
            border: OutlineInputBorder(),
          ),
        ),
        
        SizedBox(height: 8),
        
        Text('Negative Prompt', style: TextStyle(fontWeight: FontWeight.bold)),
        TextField(
          controller: _negativePromptController,
          maxLines: 2,
          decoration: InputDecoration(
            hintText: 'What to avoid in the generation...',
            border: OutlineInputBorder(),
          ),
        ),
        
        // Add prompt template chips here
        _buildPromptTemplateChips(),
      ],
    );
  }
  
  Widget _buildPromptTemplateChips() {
    // Implementation for template chips
    return Container(
      height: 40,
      child: ListView(
        scrollDirection: Axis.horizontal,
        children: [
          // Gold chips for prompt terms
          ActionChip(
            avatar: CircleAvatar(backgroundColor: Colors.amber),
            label: Text('high quality'),
            onPressed: () => _appendToPrompt('high quality'),
          ),
          SizedBox(width: 8),
          ActionChip(
            avatar: CircleAvatar(backgroundColor: Colors.amber),
            label: Text('detailed'),
            onPressed: () => _appendToPrompt('detailed'),
          ),
          
          SizedBox(width: 16),
          
          // Green chips for templates
          ActionChip(
            avatar: CircleAvatar(backgroundColor: Colors.green),
            label: Text('Portrait'),
            onPressed: () => _applyTemplate('portrait'),
          ),
          SizedBox(width: 8),
          ActionChip(
            avatar: CircleAvatar(backgroundColor: Colors.green),
            label: Text('Landscape'),
            onPressed: () => _applyTemplate('landscape'),
          ),
        ],
      ),
    );
  }
  
  void _appendToPrompt(String term) {
    final currentText = _promptController.text;
    final newText = currentText.isEmpty ? term : '$currentText, $term';
    _promptController.text = newText;
    _promptController.selection = TextSelection.fromPosition(
      TextPosition(offset: newText.length),
    );
  }
  
  void _applyTemplate(String templateName) {
    // Fetch template from repository and apply it
    final templates = ref.read(templateRepositoryProvider);
    final template = templates.getTemplateByName(templateName);
    
    if (template != null) {
      _promptController.text = template.promptText;
      if (template.negativePrompt != null && template.negativePrompt!.isNotEmpty) {
        _negativePromptController.text = template.negativePrompt!;
      }
    }
  }
  
  Widget _buildParametersSection() {
    final selectedModel = ref.watch(selectedModelProvider);
    final modelInfo = ref.read(modelCacheProvider).getModelByKey(selectedModel.modelKey!);
    
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Generation Parameters', style: TextStyle(fontWeight: FontWeight.bold)),
            
            SizedBox(height: 8),
            
            // Current model info display
            Container(
              padding: EdgeInsets.all(8),
              color: Colors.blue.withOpacity(0.1),
              child: Row(
                children: [
                  Icon(Icons.model_training, size: 20),
                  SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Model: ${modelInfo?.name ?? selectedModel.modelKey}',
                      style: TextStyle(fontWeight: FontWeight.medium),
                    ),
                  ),
                ],
              ),
            ),
            
            SizedBox(height: 16),
            
            // Dimensions
            Row(
              children: [
                Expanded(
                  child: TextFormField(
                    decoration: InputDecoration(labelText: 'Width'),
                    initialValue: _parameters['width']?.toString() ?? '1024',
                    keyboardType: TextInputType.number,
                    onChanged: (value) {
                      setState(() {
                        _parameters['width'] = int.tryParse(value) ?? 1024;
                      });
                    },
                  ),
                ),
                SizedBox(width: 16),
                Expanded(
                  child: TextFormField(
                    decoration: InputDecoration(labelText: 'Height'),
                    initialValue: _parameters['height']?.toString() ?? '1024',
                    keyboardType: TextInputType.number,
                    onChanged: (value) {
                      setState(() {
                        _parameters['height'] = int.tryParse(value) ?? 1024;
                      });
                    },
                  ),
                ),
              ],
            ),
            
            // Batch size
            SizedBox(height: 16),
            Text('Generate $_batchSize images', textAlign: TextAlign.center),
            Slider(
              value: _batchSize.toDouble(),
              min: 1,
              max: 10,
              divisions: 9,
              label: _batchSize.toString(),
              onChanged: (value) {
                setState(() {
                  _batchSize = value.round();
                });
              },
            ),
            
            // Advanced parameters toggle
            ExpansionTile(
              title: Text('Advanced Parameters'),
              children: [
                // Steps
                Slider(
                  value: (_parameters['steps'] ?? 30).toDouble(),
                  min: 10,
                  max: 50,
                  divisions: 40,
                  label: _parameters['steps']?.toString() ?? '30',
                  onChanged: (value) {
                    setState(() {
                      _parameters['steps'] = value.round();
                    });
                  },
                ),
                Text('Steps: ${_parameters['steps'] ?? 30}', textAlign: TextAlign.center),
                
                // CFG Scale
                Slider(
                  value: (_parameters['cfg_scale'] ?? 7.5).toDouble(),
                  min: 1.0,
                  max: 15.0,
                  divisions: 28,
                  label: (_parameters['cfg_scale'] ?? 7.5).toString(),
                  onChanged: (value) {
                    setState(() {
                      _parameters['cfg_scale'] = value;
                    });
                  },
                ),
                Text('CFG Scale: ${_parameters['cfg_scale'] ?? 7.5}', textAlign: TextAlign.center),
                
                // Scheduler
                DropdownButtonFormField<String>(
                  decoration: InputDecoration(labelText: 'Scheduler'),
                  value: _parameters['scheduler'] ?? 'euler',
                  items: ['euler', 'euler_ancestral', 'dpm_2', 'dpm_2_ancestral', 'dpmpp_2m']
                      .map((s) => DropdownMenuItem(value: s, child: Text(s)))
                      .toList(),
                  onChanged: (value) {
                    if (value != null) {
                      setState(() {
                        _parameters['scheduler'] = value;
                      });
                    }
                  },
                ),
                
                // Random Seed Toggle
                SwitchListTile(
                  title: Text('Use Random Seed'),
                  value: !_parameters.containsKey('seed'),
                  onChanged: (value) {
                    setState(() {
                      if (value) {
                        _parameters.remove('seed');
                      } else {
                        _parameters['seed'] = Random().nextInt(1000000);
                      }
                    });
                  },
                ),
                
                // Seed input (only if random seed is off)
                if (_parameters.containsKey('seed'))
                  TextFormField(
                    decoration: InputDecoration(labelText: 'Seed'),
                    initialValue: _parameters['seed']?.toString() ?? '',
                    keyboardType: TextInputType.number,
                    onChanged: (value) {
                      setState(() {
                        _parameters['seed'] = int.tryParse(value) ?? Random().nextInt(1000000);
                      });
                    },
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }
  
  Widget _buildActionButtons() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.end,
      children: [
        OutlinedButton(
          onPressed: () {
            // Cancel current step
            ref.read(generationStepProvider.notifier).cancelStep();
          },
          child: Text('Cancel'),
        ),
        SizedBox(width: 16),
        ElevatedButton(
          onPressed: _canGenerate() ? () => _generateImages() : null,
          child: Text('Generate'),
        ),
      ],
    );
  }
  
  bool _canGenerate() {
    final hasPrompt = _promptController.text.isNotEmpty;
    final hasModel = ref.read(selectedModelProvider).modelKey != null;
    return hasPrompt && hasModel;
  }
  
  void _generateImages() {
    final sessionId = ref.read(generationSessionProvider).currentSession?.id;
    if (sessionId == null) {
      // Create a new session first
      ref.read(generationSessionProvider.notifier).createSession('scratch', null).then((session) {
        _submitGeneration(session.id);
      });
    } else {
      _submitGeneration(sessionId);
    }
  }
  
  void _submitGeneration(String sessionId) {
    final selectedModel = ref.read(selectedModelProvider);
    
    // Ensure we have model and VAE info
    if (selectedModel.modelKey == null || selectedModel.modelHash == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Please select a model first'))
      );
      return;
    }
    
    // Update parameters
    _parameters['batch_size'] = _batchSize;
    _parameters['model_key'] = selectedModel.modelKey;
    _parameters['model_hash'] = selectedModel.modelHash;
    
    // Add VAE info if available
    if (selectedModel.vaeKey != null && selectedModel.vaeHash != null) {
      _parameters['vae_key'] = selectedModel.vaeKey;
      _parameters['vae_hash'] = selectedModel.vaeHash;
    }
    
    // Generate a correlation ID for tracking
    final correlationId = 'gen_${DateTime.now().millisecondsSinceEpoch}_${Random().nextInt(10000)}';
    
    ref.read(generationStepProvider.notifier).createStep(
      sessionId: sessionId,
      prompt: _promptController.text,
      negativePrompt: _negativePromptController.text,
      parameters: _parameters,
      correlationId: correlationId,
      parentId: widget.step?.id,
    );
  }
}