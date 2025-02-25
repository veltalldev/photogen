# Updated Frontend Implementation Guide

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

// Generation workflow providers
final generationSessionProvider = StateNotifierProvider<GenerationSessionNotifier, GenerationSessionState>((ref) {
  return GenerationSessionNotifier(
    ref.watch(invokeAIClientProvider),
    ref.watch(photoRepositoryProvider),
  );
}
```

## Additional Required Components

The following components will also need to be implemented to complete the frontend:

### 1. Session History View
```dart
class SessionHistoryView extends ConsumerWidget {
  // Displays a list of all previous generation sessions
  // Allows loading a previous session for continuation or review
  // Shows thumbnails of key images from each session
  // Includes session dates, completion status, and entry type
}
```

### 2. Timeline Navigation Component
```dart
class TimelineNavigationComponent extends ConsumerWidget {
  // Provides swipe-based navigation through step history
  // Visualizes branches and alternative selections
  // Allows jumping to any point in the session history
  // Displays parameter changes between steps
}
```

### 3. Image Comparison Tool
```dart
class ImageComparisonTool extends ConsumerWidget {
  // Side-by-side or overlay comparison of images
  // Highlights differences between iterations
  • Supports comparing current image with source or previous steps
  // Includes parameter comparison to help understand differences
}
```

### 4. Retrieval Status Manager
```dart
class RetrievalStatusManager extends ConsumerWidget {
  // Monitors and displays retrieval status for all images
  // Provides batch retry functionality for failed retrievals
  // Shows progress for ongoing retrievals
  // Handles background retry scheduling
}
```

### 5. Model Selection Interface
```dart
class ModelSelectionInterface extends ConsumerWidget {
  // Lists available models with metadata
  // Provides filtering and favorites
  // Shows model compatibility information
  // Includes performance recommendations
}
```

### 6. Generation Queue Monitor
```dart
class GenerationQueueMonitor extends ConsumerWidget {
  // Displays status of queued and active generation jobs
  // Shows estimated completion times
  // Allows cancellation of pending jobs
  • Provides detailed progress information
}
```

### 7. Session Completion Dialog
```dart
class SessionCompletionDialog extends ConsumerWidget {
  // Provides final review of all generated images
  • Allows selecting which images to keep/discard
  • Shows session statistics (steps, alternatives, time spent)
  • Offers options for organizing results (albums, tags)
}
```

### 8. Alert and Notification System
```dart
class NotificationManager extends ConsumerWidget {
  // Handles system notifications for long-running operations
  • Displays alerts for errors, retries, and completions
  • Provides non-intrusive status updates
  • Centralizes error handling UI
}
```

### 9. Settings Interface
```dart
class BackendSettingsInterface extends ConsumerWidget {
  • Configures backend connection preferences
  • Sets default values for generation parameters
  • Manages RunPod API keys and settings
  • Controls automatic shutdown timing
}
```

### 10. Prompt Template Manager
```dart
class PromptTemplateManager extends ConsumerWidget {
  // Interface for creating and editing templates
  • Provides organization of templates into categories
  • Includes import/export functionality
  • Manages template favorites and history
}
```

## Testing Strategy

The testing approach for these components should follow the patterns outlined in the original guide, with special attention to:

1. **Network failure scenarios** for remote backends
2. **State transitions** in the generation workflow
3. **UI responsiveness** during long-running operations
4. **Error recovery** from various failure points
5. **Cross-device compatibility** for responsive layouts

## Implementation Priorities

1. **Core Workflow** (Session Manager, Step Editor, Alternatives Grid)
2. **Backend Connectivity** (Backend Status Widget, Retrieval Status Manager)
3. **Navigation Components** (Timeline Navigation, Session History)
4. **Enhancement Tools** (Image Comparison, Template Manager)
5. **Administrative Features** (Settings Interface, Completion Dialog)

This prioritization ensures a functional workflow can be implemented quickly, with refinements added incrementally.);

final generationStepProvider = StateNotifierProvider<GenerationStepNotifier, GenerationStepState>((ref) {
  return GenerationStepNotifier(
    ref.watch(invokeAIClientProvider),
    ref.watch(photoRepositoryProvider),
  );
});

// Remote backend state
final backendStatusProvider = StateNotifierProvider<BackendStatusNotifier, BackendStatus>((ref) {
  return BackendStatusNotifier(
    ref.watch(backendManagerProvider),
    ref.watch(settingsProvider),
  );
});

// State classes
class BackendStatus {
  final bool isRemote;
  final bool isConnected;
  final String baseUrl;
  final String? podId;
  final String? podStatus;
  final DateTime? lastActivity;
  final Duration? uptime;
  final double? currentCost;
  
  const BackendStatus({
    required this.isRemote,
    required this.isConnected,
    required this.baseUrl,
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
  
  const GenerationSessionState({
    this.currentSession,
    this.steps = const [],
    this.isLoading = false,
    this.error,
  });
}

class GenerationStepState {
  final GenerationStep? currentStep;
  final List<StepAlternative> alternatives;
  final bool isLoading;
  final String? error;
  
  const GenerationStepState({
    this.currentStep,
    this.alternatives = const [],
    this.isLoading = false,
    this.error,
  });
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
```

### Image Loading & Display

#### Progressive Loading Implementation with Retrieval Status
```dart
class ProgressiveImageWidget extends StatelessWidget {
  final String photoId;
  final bool enableAnimation;

  Widget build(BuildContext context) {
    return Consumer(builder: (context, ref, _) {
      final photo = ref.watch(photoProvider(photoId));
      
      // Handle retrieval status
      if (photo.retrieval_status == 'pending' || photo.retrieval_status == 'failed') {
        return Stack(
          children: [
            // Placeholder or low-res preview
            Container(
              color: Colors.grey.shade200,
              child: Center(
                child: photo.retrieval_status == 'pending'
                    ? CircularProgressIndicator()
                    : IconButton(
                        icon: Icon(Icons.refresh),
                        onPressed: () => ref.read(photoRepositoryProvider).retryRetrieval(photoId),
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
        // Backend is connected, get additional info for remote backends
        if (isRemote) {
          final podStatus = await _getPodStatus();
          return BackendStatus(
            isRemote: true,
            isConnected: true,
            baseUrl: baseUrl,
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
  }
  
  Future<bool> switchMode(bool useRemote) async {
    // Implementation to switch between local and remote mode
  }
  
  Future<Map<String, dynamic>> startPod() async {
    // Implementation to start remote pod
  }
  
  Future<bool> stopPod() async {
    // Implementation to stop remote pod
  }
}
```

## Generation Workflow UI Components

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
  String? _selectedModelId;
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
    _parameters = Map<String, dynamic>.from(step?.parameters ?? {
      'width': 1024,
      'height': 1024,
      'steps': 30,
      'cfg_scale': 7.5,
      'scheduler': 'euler',
    });
    _selectedModelId = step?.model_id;
    _batchSize = step?.parameters['batch_size'] ?? 4;
  }
  
  @override
  Widget build(BuildContext context) {
    final models = ref.watch(modelsProvider);
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        // Prompt editor
        _buildPromptEditor(),
        
        SizedBox(height: 16),
        
        // Generation parameters
        _buildParametersSection(models),
        
        SizedBox(height: 16),
        
        // Action buttons
        _buildActionButtons(),
      ],
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
    // Implementation to apply template
  }
  
  Widget _buildParametersSection(AsyncValue<List<Model>> models) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Generation Parameters', style: TextStyle(fontWeight: FontWeight.bold)),
            
            // Model selection
            DropdownButtonFormField<String>(
              decoration: InputDecoration(labelText: 'Model'),
              value: _selectedModelId,
              items: models.when(
                data: (data) => data.map((model) => DropdownMenuItem(
                  value: model.id,
                  child: Text(model.name),
                )).toList(),
                loading: () => [],
                error: (_, __) => [],
              ),
              onChanged: (value) {
                if (value != null) {
                  setState(() {
                    _selectedModelId = value;
                  });
                }
              },
            ),
            
            // Dimensions, steps, etc.
            Row(
              children: [
                Expanded(
                  child: TextFormField(
                    decoration: InputDecoration(labelText: 'Width'),
                    initialValue: _parameters['width'].toString(),
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
                    initialValue: _parameters['height'].toString(),
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
            Text('Generate $_batchSize images', textAlign: TextAlign.center),
            
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
                  label: _parameters['steps'].toString(),
                  onChanged: (value) {
                    setState(() {
                      _parameters['steps'] = value.round();
                    });
                  },
                ),
                Text('Steps: ${_parameters['steps']}', textAlign: TextAlign.center),
                
                // CFG Scale
                Slider(
                  value: (_parameters['cfg_scale'] ?? 7.5),
                  min: 1.0,
                  max: 15.0,
                  divisions: 28,
                  label: _parameters['cfg_scale'].toString(),
                  onChanged: (value) {
                    setState(() {
                      _parameters['cfg_scale'] = value;
                    });
                  },
                ),
                Text('CFG Scale: ${_parameters['cfg_scale']}', textAlign: TextAlign.center),
                
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
    return _promptController.text.isNotEmpty && _selectedModelId != null;
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
    _parameters['batch_size'] = _batchSize;
    
    ref.read(generationStepProvider.notifier).createStep(
      sessionId: sessionId,
      prompt: _promptController.text,
      negativePrompt: _negativePromptController.text,
      parameters: _parameters,
      modelId: _selectedModelId!,
      parentId: widget.step?.id,
    );
  }
}
```

### Alternatives Grid

```dart
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
                  Text('Model: ${step.model_id}'),
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

### Backend Status Widget

```dart
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
                  '\${backendStatus.currentCost!.toStringAsFixed(2)}',
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
                