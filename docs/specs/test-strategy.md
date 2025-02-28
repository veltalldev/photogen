# Updated Testing Strategy Guide

## 1. Development Workflow

### 1.1 Planning Phase
For each unit of work:
1. Define the scope and boundaries
2. Identify integration points
3. List expected behaviors
4. Define error scenarios
5. Document API contract

### 1.2 Test Planning
Before implementation:
1. Write unit tests for core logic
2. Define integration test scenarios
3. Identify error cases to test
4. Plan performance test cases if relevant
5. Define InvokeAI-specific test cases for generation workflows

### 1.3 Implementation
Follow test-driven approach:
1. Write failing test
2. Implement functionality
3. Pass test
4. Refactor
5. Document

### 1.4 Documentation
After implementation:
1. Update API documentation
2. Add usage examples
3. Document error scenarios
4. Update relevant architecture docs
5. Document any InvokeAI-specific considerations or limitations

## 2. Testing Levels

### 2.1 Unit Tests
Test isolated components:
- Database models
- Service methods
- Utility functions
- Data transformations
- Graph building components
- Model cache operations

Example:
```python
def test_photo_creation():
    # Arrange
    photo_data = {
        "filename": "test.jpg",
        "width": 1920,
        "height": 1080
    }
    
    # Act
    photo = Photo.create(photo_data)
    
    # Assert
    assert photo.filename == "test.jpg"
    assert photo.width == 1920
    assert photo.height == 1080
```

### 2.2 Integration Tests
Test component interactions:
- API endpoints
- Database operations
- File system operations
- InvokeAI integration
- Image retrieval and storage
- Model querying and caching

Example:
```python
async def test_photo_upload_flow():
    # Arrange
    file_content = create_test_image()
    
    # Act
    response = await client.post("/photos", files={"file": file_content})
    photo_id = response.json()["id"]
    
    # Assert
    assert response.status_code == 201
    assert await database.photos.exists(photo_id)
    assert os.path.exists(f"uploads/{photo_id}.jpg")
```

### 2.3 InvokeAI Integration Tests
Test specific interactions with InvokeAI API:

#### 2.3.1 Model Management Tests
```python
async def test_model_retrieval_and_caching():
    # Arrange
    mock_invokeai = MockInvokeAIClient()
    model_cache = ModelCacheService()
    
    # Act
    models = await mock_invokeai.get_models()
    model_cache.update_models(models)
    cached_models = model_cache.get_all_models()
    
    # Assert
    assert len(models) > 0
    assert len(cached_models) == len(models)
    assert model_cache.has_valid_cache() == True
```

#### 2.3.2 Graph Generation Tests
```python
def test_graph_builder_creates_valid_graph():
    # Arrange
    params = GenerationParameters(
        prompt="Test prompt",
        model_key="test-model-key",
        model_hash="blake3:abc123",
        vae_key="test-vae-key",
        vae_hash="blake3:def456"
    )
    graph_builder = GraphBuilder(MockModelCacheService())
    
    # Act
    graph = graph_builder.build_generation_graph(params)
    
    # Assert
    assert "batch" in graph
    assert "graph" in graph["batch"]
    assert "nodes" in graph["batch"]["graph"]
    assert "edges" in graph["batch"]["graph"]
    
    # Verify critical nodes exist
    nodes = graph["batch"]["graph"]["nodes"]
    assert any(node["type"] == "sdxl_model_loader" for node in nodes.values())
    assert any(node["type"] == "sdxl_compel_prompt" for node in nodes.values())
    assert any(node["type"] == "noise" for node in nodes.values())
    
    # Verify metadata propagation
    data_section = graph["batch"]["data"][0]
    assert any(item["field_name"] == "positive_prompt" for item in data_section)
```

#### 2.3.3 Batch Processing Tests
```python
async def test_batch_status_monitoring():
    # Arrange
    mock_invokeai = MockInvokeAIClient()
    batch_id = "test-batch-123"
    
    # Act - simulate a batch that takes multiple polls to complete
    status1 = await mock_invokeai.get_batch_status(batch_id)
    await mock_invokeai.advance_batch_progress(batch_id, 0.5)
    status2 = await mock_invokeai.get_batch_status(batch_id)
    await mock_invokeai.advance_batch_progress(batch_id, 1.0)
    status3 = await mock_invokeai.get_batch_status(batch_id)
    
    # Assert
    assert status1.is_complete() == False
    assert status1.calculate_progress() < 100
    
    assert status2.is_complete() == False
    assert status2.calculate_progress() > status1.calculate_progress()
    
    assert status3.is_complete() == True
    assert status3.calculate_progress() == 100
    assert len(status3.get_completed_image_names()) > 0
```

#### 2.3.4 Image Retrieval Tests
```python
async def test_image_retrieval_with_correlation():
    # Arrange
    mock_invokeai = MockInvokeAIClient()
    retrieval_service = ImageRetrievalService(
        invokeai_client=mock_invokeai,
        photo_repository=MockPhotoRepository(),
        file_service=MockFileService()
    )
    batch_id = "test-batch-456"
    correlation_id = "test-correlation-789"
    session_id = uuid.uuid4()
    step_id = uuid.uuid4()
    
    # Generate mock images with the correlation ID
    await mock_invokeai.generate_with_correlation(batch_id, correlation_id, 4)
    
    # Act
    result = await retrieval_service.retrieve_batch_images(
        batch_id, 
        expected_count=4,
        session_id=session_id,
        step_id=step_id,
        correlation_id=correlation_id
    )
    
    # Assert
    assert result.total == 4
    assert result.retrieved == 4
    assert result.failed == 0
    
    # Verify all images were properly stored
    stored_photos = await MockPhotoRepository().list_by_step(step_id)
    assert len(stored_photos) == 4
    for photo in stored_photos:
        assert photo.invoke_id is not None
        assert photo.retrieval_status == 'completed'
```

### 2.4 Error Case Testing
Test failure scenarios:
- Invalid inputs
- Resource constraints
- Integration failures
- Concurrent operations
- Network interruptions
- InvokeAI service errors
- Retrieval failures

Example:
```python
async def test_photo_upload_invalid_format():
    # Arrange
    invalid_file = create_test_text_file()
    
    # Act
    response = await client.post("/photos", files={"file": invalid_file})
    
    # Assert
    assert response.status_code == 400
    assert "Invalid file format" in response.json()["error"]
```

#### 2.4.1 InvokeAI Error Handling Tests
```python
async def test_invokeai_connection_failure():
    # Arrange
    failing_client = MockInvokeAIClient(should_fail=True)
    generation_service = GenerationService(failing_client)
    
    # Act & Assert
    with pytest.raises(ConnectionError):
        await generation_service.generate_images(
            prompt="test prompt",
            model_key="test-model"
        )
```

```python
async def test_model_not_found_error():
    # Arrange
    mock_invokeai = MockInvokeAIClient()
    
    # Act
    result = await mock_invokeai.queue_generation(
        GenerationParameters(
            prompt="test prompt",
            model_key="non-existent-model",
            model_hash="blake3:invalid"
        )
    )
    
    # Assert
    assert "error" in result
    assert "Model not found" in result["error"]
```

```python
async def test_retrieval_retry_mechanism():
    # Arrange
    failing_client = MockInvokeAIClient(fail_retrieval_attempts=2)
    retrieval_service = ImageRetrievalService(
        invokeai_client=failing_client,
        max_retries=5
    )
    
    # Act
    result = await retrieval_service.retrieve_image("test-image-id")
    
    # Assert
    assert result is not None
    assert failing_client.retrieval_attempt_count == 3  # Initial + 2 retries
```

### 2.5 Performance Tests
Key metrics to evaluate:
1. Response times
2. Resource usage
3. Concurrent operations
4. File system operations
5. InvokeAI request/response cycles
6. Image retrieval performance
7. Model caching efficiency

Example performance test:
```python
async def test_batch_generation_performance():
    # Arrange
    mock_invokeai = MockInvokeAIClient()
    params = GenerationParameters(
        prompt="Performance test",
        model_key="test-model",
        batch_size=10  # Large batch
    )
    
    # Act
    start_time = time.time()
    result = await mock_invokeai.queue_generation(params)
    batch_id = result["batch_id"]
    
    # Wait for completion with timeout
    timeout = 60  # seconds
    completed = await mock_invokeai.wait_for_batch_completion(batch_id, timeout)
    
    total_time = time.time() - start_time
    
    # Assert
    assert completed["is_success"] == True
    assert len(completed["image_names"]) == 10
    assert total_time < timeout  # Ensure it completes within timeout
```

## 3. Testing Guidelines

### 3.1 Test Organization
- Group tests by feature/module
- Clear test naming convention
- Shared test fixtures
- Isolated test databases
- Mock InvokeAI clients for reliable testing

Example test directory structure:
```
tests/
  ├── unit/
  │    ├── models/
  │    ├── services/
  │    └── utils/
  ├── integration/
  │    ├── api/
  │    ├── database/
  │    └── filesystem/
  ├── invokeai/
  │    ├── connection/
  │    ├── graph/
  │    ├── generation/
  │    └── retrieval/
  ├── performance/
  └── conftest.py
```

### 3.2 Test Coverage
Priority areas:
1. Core business logic
2. Data integrity operations
3. File system operations
4. Error handling
5. Integration points
6. InvokeAI graph generation
7. Image retrieval workflows
8. Batch status monitoring

### 3.3 Performance Testing
Key metrics for InvokeAI integration:
1. Generation request formation time
2. Status polling efficiency
3. Image retrieval throughput
4. Concurrent retrieval performance
5. Model caching hit rates
6. Memory usage during large batches

### 3.4 Mocking Strategy

#### 3.4.1 InvokeAI API Mocking
Create a comprehensive mock implementation of InvokeAIClient:

```python
class MockInvokeAIClient:
    def __init__(self, should_fail=False, fail_retrieval_attempts=0):
        self.should_fail = should_fail
        self.fail_retrieval_attempts = fail_retrieval_attempts
        self.retrieval_attempt_count = 0
        self.batches = {}  # Track batch status
        self.generated_images = {}  # Track generated images
        self.models = self._create_mock_models()
    
    def _create_mock_models(self):
        """Create a set of mock models for testing"""
        return [
            {
                "key": "mock-model-1",
                "hash": "blake3:abc123",
                "name": "Mock Model 1",
                "type": "main",
                "base": "sdxl"
            },
            {
                "key": "mock-vae-1",
                "hash": "blake3:def456",
                "name": "Mock VAE 1",
                "type": "vae",
                "base": "sdxl"
            }
        ]
    
    async def connect(self, base_url):
        """Mock connection to InvokeAI"""
        if self.should_fail:
            raise ConnectionError("Mock connection failure")
        return True
    
    async def get_models(self, refresh=False):
        """Return mock models"""
        if self.should_fail:
            raise ConnectionError("Mock connection failure")
        return self.models
    
    async def queue_generation(self, params):
        """Mock generation request"""
        if self.should_fail:
            raise ConnectionError("Mock connection failure")
        
        # Check for model existence
        if params.model_key != "mock-model-1":
            return {"error": "Model not found"}
        
        batch_id = f"batch-{uuid.uuid4()}"
        self.batches[batch_id] = {
            "status": "pending",
            "progress": 0.0,
            "images": [],
            "params": params
        }
        
        # Start async "generation"
        asyncio.create_task(self._simulate_generation(batch_id))
        
        return {
            "batch_id": batch_id,
            "success": True
        }
    
    async def _simulate_generation(self, batch_id):
        """Simulate the generation process asynchronously"""
        batch = self.batches[batch_id]
        batch["status"] = "processing"
        
        # Simulate generation time (0.5s per image)
        await asyncio.sleep(0.5 * batch["params"].batch_size)
        
        # Create mock images
        batch["images"] = [
            f"img-{uuid.uuid4()}" for _ in range(batch["params"].batch_size)
        ]
        
        # Store image metadata for later retrieval
        for img_id in batch["images"]:
            self.generated_images[img_id] = {
                "width": batch["params"].width,
                "height": batch["params"].height,
                "prompt": batch["params"].prompt,
                "seed": batch["params"].seed or random.randint(1, 1000000),
                "model_key": batch["params"].model_key,
                "created_at": datetime.now().isoformat()
            }
        
        batch["status"] = "completed"
        batch["progress"] = 1.0
    
    async def get_batch_status(self, batch_id):
        """Get status of a batch"""
        if self.should_fail:
            raise ConnectionError("Mock connection failure")
        
        if batch_id not in self.batches:
            return {"error": "Batch not found"}
        
        batch = self.batches[batch_id]
        return {
            "batch_id": batch_id,
            "status": batch["status"],
            "progress": batch["progress"],
            "is_complete": batch["status"] == "completed",
            "calculate_progress": lambda: batch["progress"] * 100,
            "get_completed_image_names": lambda: batch["images"] if batch["status"] == "completed" else []
        }
    
    async def advance_batch_progress(self, batch_id, progress):
        """Helper to manually advance progress for testing"""
        if batch_id in self.batches:
            self.batches[batch_id]["progress"] = progress
            if progress >= 1.0:
                self.batches[batch_id]["status"] = "completed"
    
    async def generate_with_correlation(self, batch_id, correlation_id, count):
        """Generate mock images with a correlation ID"""
        self.batches[batch_id] = {
            "status": "completed",
            "progress": 1.0,
            "images": [f"img-{correlation_id}-{i}" for i in range(count)],
            "params": {"correlation_id": correlation_id}
        }
        
        # Store image metadata with correlation ID
        for img_id in self.batches[batch_id]["images"]:
            self.generated_images[img_id] = {
                "width": 1024,
                "height": 1024,
                "prompt": f"Test prompt with {correlation_id}",
                "seed": random.randint(1, 1000000),
                "correlation_id": correlation_id,
                "created_at": datetime.now().isoformat()
            }
    
    async def get_image(self, image_id):
        """Mock image retrieval"""
        self.retrieval_attempt_count += 1
        
        if self.retrieval_attempt_count <= self.fail_retrieval_attempts:
            # Simulate failure for specified number of attempts
            raise ConnectionError("Mock retrieval failure")
        
        if image_id not in self.generated_images:
            return None
        
        # Return mock image data (1x1 transparent PNG)
        return base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
        )
    
    async def get_thumbnail(self, image_id):
        """Mock thumbnail retrieval"""
        # Same implementation as get_image for simplicity
        return await self.get_image(image_id)
    
    async def get_image_metadata(self, image_id):
        """Mock metadata retrieval"""
        if image_id not in self.generated_images:
            return None
        
        return self.generated_images[image_id]
```

When to mock:
1. External services (InvokeAI)
2. File system operations
3. Time-dependent operations
4. Resource-intensive operations
5. Network communications

Example:
```python
@pytest.fixture
def mock_invokeai():
    with patch("services.invokeai.InvokeAIClient") as mock:
        mock.generate.return_value = {"id": "test_generation"}
        yield mock

async def test_image_generation(mock_invokeai):
    # Arrange
    generation_params = {
        "prompt": "test prompt",
        "num_images": 1
    }
    
    # Act
    result = await generation_service.generate(generation_params)
    
    # Assert
    assert result.batch_id == "test_generation"
    mock_invokeai.generate.assert_called_once_with(generation_params)
```

## 4. Documentation Integration

### 4.1 Test Documentation
Each test should document:
- Purpose of test
- Input conditions
- Expected outcomes
- Error scenarios
- Performance expectations
- InvokeAI-specific behaviors being tested

### 4.2 API Documentation
Update with each change:
- Endpoint behavior
- Request/response formats
- Error responses
- Examples
- InvokeAI integration details

### 4.3 Architecture Documentation
Keep updated:
- Component interactions
- Data flow
- Error handling
- Resource management
- Graph building patterns
- Retrieval strategies

## 5. InvokeAI-Specific Test Cases

These test cases focus on testing the integration with InvokeAI's API, with special attention to the unique challenges identified during implementation testing.

### 5.1 Connection Testing
Test different connection scenarios:
- Local mode connection
- Remote mode connection
- Connection failures
- API version compatibility
- RunPod initialization

```python
async def test_local_connection():
    # Arrange
    settings = Settings(use_remote_backend=False, local_backend_url="http://localhost:9090")
    backend_manager = BackendManager(settings)
    
    # Act
    status = await backend_manager.get_status()
    
    # Assert
    assert status.is_remote == False
    assert status.is_connected == True
    assert status.base_url == "http://localhost:9090"
```

```python
async def test_remote_connection():
    # Arrange
    settings = Settings(
        use_remote_backend=True,
        remote_backend_url="https://pod-id-9090.proxy.runpod.net"
    )
    backend_manager = BackendManager(settings)
    
    # Act
    status = await backend_manager.get_status()
    
    # Assert
    assert status.is_remote == True
    assert status.is_connected == True
    assert "runpod.net" in status.base_url
```

### 5.2 Model Management Testing
Test model handling logic:
- Model retrieval and parsing
- Cache creation and invalidation
- Compatibility detection
- VAE pairing
- Parameter validation

```python
async def test_model_cache_ttl():
    # Arrange
    model_cache = ModelCacheService(ttl=timedelta(minutes=15))
    
    # Act
    model_cache.update_models(create_test_models())
    is_valid_before = model_cache.has_valid_cache()
    
    # Fast-forward time by 16 minutes
    with freeze_time(datetime.now() + timedelta(minutes=16)):
        is_valid_after = model_cache.has_valid_cache()
    
    # Assert
    assert is_valid_before == True
    assert is_valid_after == False
```

```python
def test_vae_compatibility_detection():
    # Arrange
    models = [
        create_test_model(key="model1", base="sdxl"),
        create_test_model(key="model2", base="sd15"),
        create_test_vae(key="vae1", base="sdxl"),
        create_test_vae(key="vae2", base="sdxl"),
        create_test_vae(key="vae3", base="sd15")
    ]
    
    model_service = ModelService()
    
    # Act
    model_service.process_models(models)
    sdxl_vaes = model_service.get_compatible_vaes("model1")
    sd15_vaes = model_service.get_compatible_vaes("model2")
    
    # Assert
    assert len(sdxl_vaes) == 2
    assert sdxl_vaes[0].key == "vae1"
    assert sdxl_vaes[1].key == "vae2"
    
    assert len(sd15_vaes) == 1
    assert sd15_vaes[0].key == "vae3"
```

### 5.3 Graph Building Tests
Test the graph construction logic:
- Node creation
- Edge connection
- Parameter propagation 
- Metadata handling
- Graph validation

```python
def test_complete_graph_structure():
    # Arrange
    params = GenerationParameters(
        prompt="Test graph",
        model_key="test-model",
        model_hash="blake3:test",
        vae_key="test-vae",
        vae_hash="blake3:test-vae"
    )
    graph_builder = GraphBuilder(MockModelCacheService())
    
    # Act
    graph = graph_builder.build_generation_graph(params)
    
    # Assert
    assert "batch" in graph
    batch = graph["batch"]
    assert "graph" in batch
    
    # Check node types
    nodes = batch["graph"]["nodes"]
    node_types = [node["type"] for node in nodes.values()]
    required_types = [
        "sdxl_model_loader", 
        "sdxl_compel_prompt", 
        "collect", 
        "noise", 
        "denoise_latents",
        "vae_loader",
        "core_metadata",
        "l2i"
    ]
    
    for req_type in required_types:
        assert req_type in node_types
    
    # Check metadata propagation in data section
    data_items = batch["data"][0]
    metadata_fields = [item["field_name"] for item in data_items 
                      if item["node_path"].startswith("core_metadata")]
    
    assert "positive_prompt" in metadata_fields
    assert "seed" in metadata_fields
```

### 5.4 Image Correlation Tests
Test strategies for correlating InvokeAI-generated images with requests:
- Timestamp-based correlation
- Correlation ID tracking
- Batch completion verification

```python
async def test_timestamp_correlation():
    # Arrange
    mock_invokeai = MockInvokeAIClient()
    image_service = ImageService(mock_invokeai)
    
    # Generate some images with timestamps
    completion_time = datetime.now()
    await mock_invokeai.simulate_batch_completion(
        "batch1", 
        ["img1", "img2"], 
        completion_time
    )
    
    # Act
    correlated_images = await image_service.correlate_images_by_timestamp(
        completion_time - timedelta(seconds=1),
        expected_count=2
    )
    
    wrong_time_images = await image_service.correlate_images_by_timestamp(
        completion_time - timedelta(minutes=5),
        expected_count=2
    )
    
    # Assert
    assert len(correlated_images) == 2
    assert "img1" in correlated_images
    assert "img2" in correlated_images
    
    assert len(wrong_time_images) == 0  # Should find nothing with wrong timestamp
```

```python
async def test_correlation_id_verification():
    # Arrange
    mock_invokeai = MockInvokeAIClient()
    correlation_id = "test-correlation-123"
    
    # Generate images with correlation ID in metadata
    await mock_invokeai.generate_with_correlation("batch1", correlation_id, 3)
    
    # Act
    image_service = ImageService(mock_invokeai)
    found_images = await image_service.find_images_by_correlation_id(
        correlation_id,
        expected_count=3
    )
    
    wrong_id_images = await image_service.find_images_by_correlation_id(
        "wrong-id",
        expected_count=3
    )
    
    # Assert
    assert len(found_images) == 3
    for img in found_images:
        assert correlation_id in img
    
    assert len(wrong_id_images) == 0
```

### 5.5 Retrieval Workflow Tests
Test the complete image retrieval process:
- Batch retrieval
- Error handling
- Retries
- Storage organization

```python
async def test_complete_retrieval_workflow():
    # Arrange
    mock_invokeai = MockInvokeAIClient()
    file_service = MockFileService()
    db_service = MockDatabaseService()
    retrieval_service = ImageRetrievalService(
        invokeai_client=mock_invokeai,
        file_service=file_service,
        db_service=db_service
    )
    
    # Create a completed batch
    batch_id = "test-batch"
    await mock_invokeai.generate_with_correlation(batch_id, "test-corr", 4)
    
    # Act
    session_id = uuid.uuid4()
    step_id = uuid.uuid4()
    result = await retrieval_service.retrieve_batch_images(
        batch_id=batch_id,
        expected_count=4,
        session_id=session_id,
        step_id=step_id
    )
    
    # Assert
    assert result.total == 4
    assert result.retrieved == 4
    assert result.failed == 0
    
    # Check database records
    db_photos = await db_service.get_photos_by_step(step_id)
    assert len(db_photos) == 4
    
    # Check file storage
    for photo in db_photos:
        assert file_service.file_exists(photo.local_storage_path)
        assert file_service.file_exists(photo.local_thumbnail_path)
        
    # Check storage organization
    path_pattern = f"data/photos/generated/sessions/{session_id}/{step_id}/variants/"
    for photo in db_photos:
        assert path_pattern in photo.local_storage_path
```

```python
async def test_partial_retrieval_recovery():
    # Arrange
    # Create a client that fails on every other retrieval
    mock_invokeai = MockInvokeAIClient(fail_pattern="alternating")
    retrieval_service = ImageRetrievalService(
        invokeai_client=mock_invokeai,
        file_service=MockFileService(),
        db_service=MockDatabaseService()
    )
    
    # Create a completed batch
    batch_id = "test-batch"
    await mock_invokeai.generate_with_correlation(batch_id, "test-corr", 4)
    
    # Act
    session_id = uuid.uuid4()
    step_id = uuid.uuid4()
    result = await retrieval_service.retrieve_batch_images(
        batch_id=batch_id,
        expected_count=4,
        session_id=session_id,
        step_id=step_id
    )
    
    # Now retry the failed ones
    retry_result = await retrieval_service.retry_failed_retrievals(step_id)
    
    # Assert
    assert result.total == 4
    assert result.retrieved == 2  # Only half succeed on first try
    assert result.failed == 2
    
    assert retry_result.retried == 2
    assert retry_result.succeeded == 2
    assert retry_result.failed == 0
    
    # Check database records after recovery
    db_photos = await MockDatabaseService().get_photos_by_step(step_id)
    for photo in db_photos:
        assert photo.retrieval_status == 'completed'
```

### 5.6 Remote Backend Tests
Test remote backend operations:
- Pod management
- Status monitoring
- Cost tracking
- Idle shutdown
- Error recovery

```python
async def test_pod_lifecycle():
    # Arrange
    mock_runpod = MockRunPodClient()
    backend_manager = BackendManager(
        settings=Settings(use_remote_backend=True),
        runpod_client=mock_runpod
    )
    
    # Act - Start pod
    start_result = await backend_manager.start_pod()
    pod_id = start_result["pod_id"]
    
    # Check status
    status_after_start = await backend_manager.get_pod_status(pod_id)
    
    # Stop pod
    stop_result = await backend_manager.stop_pod(pod_id)
    
    # Check status again
    status_after_stop = await backend_manager.get_pod_status(pod_id)
    
    # Assert
    assert start_result["success"] == True
    assert status_after_start["status"] == "running"
    
    assert stop_result["success"] == True
    assert stop_result["session_duration"] > 0
    assert status_after_stop["status"] == "stopped"
```

```python
async def test_cost_tracking():
    # Arrange
    mock_runpod = MockRunPodClient()
    cost_service = CostTrackingService(
        runpod_client=mock_runpod,
        database=MockDatabaseService()
    )
    
    # Create a pod session
    pod_id = "test-pod-123"
    session_start = datetime.now() - timedelta(hours=2)  # 2 hour session
    session_end = datetime.now()
    
    # Act
    await cost_service.record_session_cost(
        pod_id=pod_id,
        session_start=session_start,
        session_end=session_end,
        pod_type="NVIDIA A5000"
    )
    
    # Get cost history
    cost_history = await cost_service.get_cost_history()
    total_cost = await cost_service.get_total_cost()
    
    # Assert
    assert len(cost_history) == 1
    assert cost_history[0]["pod_id"] == pod_id
    assert cost_history[0]["duration_seconds"] == 7200  # 2 hours
    assert cost_history[0]["estimated_cost"] > 0
    assert total_cost > 0
```

```python
async def test_pod_failure_recovery():
    # Arrange
    mock_runpod = MockRunPodClient(fail_on_nth_request=2)  # Fail the second request
    backend_manager = BackendManager(
        settings=Settings(use_remote_backend=True),
        runpod_client=mock_runpod
    )
    
    # Act - Start pod successfully
    start_result = await backend_manager.start_pod()
    pod_id = start_result["pod_id"]
    
    # This request should fail
    with pytest.raises(ConnectionError):
        await backend_manager.get_pod_status(pod_id)
    
    # Recovery attempt should succeed
    recovery_status = await backend_manager.recover_connection()
    final_status = await backend_manager.get_pod_status(pod_id)
    
    # Assert
    assert recovery_status is True
    assert final_status["status"] == "running"
    assert mock_runpod.request_count == 3  # Initial, failed, and recovery
```

## 6. Frontend Testing

### 6.1 UI Component Tests
Test React components:
- Model selection interface
- Prompt editor
- Step visualization
- Alternatives grid
- Retrieval status indicators

Example component test:
```dart
testWidgets('ModelSelector shows models and handles selection', (WidgetTester tester) async {
  // Arrange
  final mockModels = [
    Model(
      id: 'model1',
      key: 'key1',
      hash: 'hash1',
      name: 'Test Model 1',
      type: 'main',
      base: 'sdxl',
      compatibleVaes: [],
      defaults: GenerationDefaults(),
    ),
    Model(
      id: 'model2',
      key: 'key2',
      hash: 'hash2',
      name: 'Test Model 2',
      type: 'main',
      base: 'sd15',
      compatibleVaes: [],
      defaults: GenerationDefaults(),
    ),
  ];
  
  // Setup test provider scope
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        modelsProvider.overrideWithValue(AsyncValue.data(mockModels)),
        selectedModelProvider.overrideWith(
          (ref) => SelectedModelNotifier(MockModelCacheService())
        ),
      ],
      child: MaterialApp(
        home: Scaffold(
          body: ModelSelectionWidget(),
        ),
      ),
    ),
  );
  
  // Act & Assert
  expect(find.text('Test Model 1'), findsOneWidget);
  expect(find.text('Test Model 2'), findsOneWidget);
  
  // Tap the first model
  await tester.tap(find.text('Test Model 1'));
  await tester.pump();
  
  // Verify selection was updated
  final container = ProviderContainer();
  final selectedModel = container.read(selectedModelProvider);
  expect(selectedModel.modelKey, 'key1');
  expect(selectedModel.modelHash, 'hash1');
});
```

### 6.2 State Management Tests
Test Riverpod providers and state management:
- Session state transitions
- Step creation and update
- Model selection logic
- Retrieval status updates

```dart
test('GenerationSessionNotifier handles session creation', () async {
  // Arrange
  final container = ProviderContainer(
    overrides: [
      invokeAIClientProvider.overrideWithValue(MockInvokeAIClient()),
      photoRepositoryProvider.overrideWithValue(MockPhotoRepository()),
      modelCacheProvider.overrideWithValue(MockModelCacheService()),
    ],
  );
  
  // Initial state should have no session
  final initialState = container.read(generationSessionProvider);
  expect(initialState.currentSession, isNull);
  
  // Act
  await container.read(generationSessionProvider.notifier).createSession('scratch', null);
  
  // Assert
  final updatedState = container.read(generationSessionProvider);
  expect(updatedState.currentSession, isNotNull);
  expect(updatedState.currentSession?.entry_type, 'scratch');
  expect(updatedState.steps, isEmpty);
});
```

### 6.3 Async UI Tests
Test async behaviors in the UI:
- Loading states
- Error handling
- Retry mechanisms
- Progress indicators

```dart
testWidgets('RetrievalStatusWidget shows correct status and allows retry', 
    (WidgetTester tester) async {
  // Arrange - Setup a failed retrieval
  final mockStep = GenerationStep(
    id: 'step1',
    session_id: 'session1',
    status: 'completed',
    batch_size: 4,
    imagesRetrieved: 2,
    imagesFailed: 2,
    imagesPending: 0,
  );
  
  // Setup providers
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        generationStepProvider.overrideWithValue(
          GenerationStepState(
            currentStep: mockStep,
            retrievalStatus: RetrievalStatus(
              total: 4,
              completed: 2,
              failed: 2,
              pending: 0,
            ),
          ),
        ),
      ],
      child: MaterialApp(
        home: Scaffold(
          body: RetrievalStatusWidget(stepId: 'step1'),
        ),
      ),
    ),
  );
  
  // Assert initial state
  expect(find.text('2 of 4 images retrieved'), findsOneWidget);
  expect(find.text('2 failed'), findsOneWidget);
  expect(find.byIcon(Icons.refresh), findsOneWidget);
  
  // Act - Tap retry button
  await tester.tap(find.byIcon(Icons.refresh));
  await tester.pump();
  
  // Verify retry was called
  final container = ProviderContainer();
  verify(container.read(generationStepProvider.notifier).retryFailedRetrievals('step1')).called(1);
});
```

## 7. Performance Testing Strategy

### 7.1 Key Metrics
When testing InvokeAI integration performance, focus on these metrics:

1. **Request Formation Time**:
   - Time to construct graph structure
   - Serialization overhead
   - Parameter validation speed

2. **Network Performance**:
   - Request latency to InvokeAI
   - Batch status polling efficiency
   - Concurrent image retrieval throughput

3. **Storage Efficiency**:
   - File write performance
   - Directory structure navigation
   - Thumbnail generation speed

4. **Memory Usage**:
   - RAM consumption during large batch processing
   - Cache efficiency for models and images
   - Memory pattern during parallel operations

### 7.2 Performance Test Cases

```python
async def test_graph_generation_performance():
    # Arrange
    graph_builder = GraphBuilder(MockModelCacheService())
    iterations = 100
    
    # Act
    start_time = time.time()
    for i in range(iterations):
        params = GenerationParameters(
            prompt=f"Test prompt {i}",
            model_key="test-model",
            model_hash="test-hash",
            vae_key="test-vae",
            vae_hash="test-vae-hash",
        )
        graph_builder.build_generation_graph(params)
    
    duration = time.time() - start_time
    avg_time = duration / iterations
    
    # Assert
    assert avg_time < 0.01  # Less than 10ms per graph construction
```

```python
async def test_concurrent_image_retrieval():
    # Arrange
    mock_invokeai = MockInvokeAIClient()
    retrieval_service = ImageRetrievalService(
        invokeai_client=mock_invokeai,
        file_service=MockFileService(),
        db_service=MockDatabaseService(),
        max_concurrent=5
    )
    
    # Generate 20 test images
    image_ids = [f"img-{i}" for i in range(20)]
    for img_id in image_ids:
        mock_invokeai.generated_images[img_id] = {"metadata": "test"}
    
    # Act
    start_time = time.time()
    result = await retrieval_service.retrieve_multiple_images(
        image_ids=image_ids,
        session_id="test-session",
        step_id="test-step"
    )
    duration = time.time() - start_time
    
    # Assert
    assert result.total == 20
    assert result.retrieved == 20
    assert duration < 2.0  # Should be fast with concurrent retrieval
```

### 7.3 Benchmarking Strategy

To properly benchmark InvokeAI integration performance:

1. **Establish Baselines**:
   - Measure performance with small, medium, and large workloads
   - Document baseline metrics for future comparison
   - Test on both development and production environments

2. **Periodic Testing**:
   - Run performance tests after significant changes
   - Track metrics over time to identify regressions
   - Set performance budgets for critical operations

3. **Load Testing**:
   - Simulate high-frequency generation requests
   - Test concurrent image retrieval limits
   - Evaluate system behavior under sustained load

4. **Edge Case Performance**:
   - Very large image dimensions
   - Many concurrent steps
   - Extended backend polling duration
   - Large model caches

## 8. Mock Implementation Guidelines

To effectively test InvokeAI integration, develop comprehensive mocks that accurately simulate API behavior.

### 8.1 Mock Classes

These mock implementations are designed to simulate the behavior of key components for testing purposes.

#### MockModelCacheService

```python
class MockModelCacheService:
    """Mock implementation of model cache service for testing"""
    
    def __init__(self):
        self._models = {
            "model1": {
                "key": "model1",
                "hash": "hash1",
                "name": "Test Model 1",
                "type": "main",
                "base": "sdxl",
                "compatibleVaes": [
                    {
                        "key": "vae1",
                        "hash": "vae-hash1",
                        "name": "Test VAE 1",
                        "isDefault": True
                    }
                ],
                "defaults": {
                    "width": 1024,
                    "height": 1024,
                    "steps": 30,
                    "cfgScale": 7.5,
                    "scheduler": "euler"
                }
            }
        }
        self._last_update = datetime.now()
    
    def has_valid_cache(self):
        """Check if cache is valid"""
        return True
    
    def get_all_models(self):
        """Get all models"""
        return list(self._models.values())
    
    def get_model_by_key(self, key):
        """Get model by key"""
        return self._models.get(key)
    
    def get_default_vae_for_model(self, model_key):
        """Get default VAE for model"""
        model = self._models.get(model_key)
        if not model or not model["compatibleVaes"]:
            return None
        
        for vae in model["compatibleVaes"]:
            if vae["isDefault"]:
                return vae
        
        return model["compatibleVaes"][0]
```

#### MockFileService

```python
class MockFileService:
    """Mock file service for testing file operations"""
    
    def __init__(self):
        self._files = {}  # path -> content
    
    async def save_file(self, path, content):
        """Save file content"""
        self._files[path] = content
        return path
    
    async def read_file(self, path):
        """Read file content"""
        if path not in self._files:
            raise FileNotFoundError(f"File not found: {path}")
        return self._files[path]
    
    def file_exists(self, path):
        """Check if file exists"""
        return path in self._files
    
    async def delete_file(self, path):
        """Delete file"""
        if path in self._files:
            del self._files[path]
            return True
        return False
    
    async def create_directory(self, path):
        """Create directory (simulated)"""
        return True
    
    def get_saved_files(self):
        """Get all saved files for verification"""
        return list(self._files.keys())
```

#### MockDatabaseService

```python
class MockDatabaseService:
    """Mock database service for testing database operations"""
    
    def __init__(self):
        self._photos = {}
        self._sessions = {}
        self._steps = {}
        self._cost_records = []
    
    async def create_photo(self, photo_data):
        """Create photo record"""
        photo_id = photo_data.get("id") or str(uuid.uuid4())
        self._photos[photo_id] = {**photo_data, "id": photo_id}
        return self._photos[photo_id]
    
    async def get_photo(self, photo_id):
        """Get photo by ID"""
        return self._photos.get(photo_id)
    
    async def update_photo(self, photo_id, updates):
        """Update photo record"""
        if photo_id in self._photos:
            self._photos[photo_id] = {**self._photos[photo_id], **updates}
            return self._photos[photo_id]
        return None
    
    async def get_photos_by_step(self, step_id):
        """Get photos associated with a step"""
        return [p for p in self._photos.values() if p.get("step_id") == step_id]
    
    async def create_session(self, session_data):
        """Create session record"""
        session_id = session_data.get("id") or str(uuid.uuid4())
        self._sessions[session_id] = {**session_data, "id": session_id}
        return self._sessions[session_id]
    
    async def create_step(self, step_data):
        """Create step record"""
        step_id = step_data.get("id") or str(uuid.uuid4())
        self._steps[step_id] = {**step_data, "id": step_id}
        return self._steps[step_id]
    
    async def update_step(self, step_id, updates):
        """Update step record"""
        if step_id in self._steps:
            self._steps[step_id] = {**self._steps[step_id], **updates}
            return self._steps[step_id]
        return None
    
    async def record_cost(self, cost_data):
        """Record cost data"""
        self._cost_records.append(cost_data)
        return cost_data
    
    async def get_cost_history(self):
        """Get cost history"""
        return self._cost_records
```

### 8.2 InvokeAI Mocking Guidelines

When mocking the InvokeAI integration, ensure your mock:

1. **Mirrors the Real API Structure**:
   - Match endpoint patterns
   - Use identical request/response formats
   - Maintain URL hierarchy

2. **Simulates Asynchronous Behavior**:
   - Add appropriate delays for realistic timing

```python
async def test_idle_shutdown():
    # Arrange
    mock_runpod = MockRunPodClient()
    backend_manager = BackendManager(
        settings=Settings(
            use_remote_backend=True,
            idle_timeout_minutes=30
        ),
        runpod_client=mock_runpod
    )
    
    # Start a pod
    start_result = await backend_manager.start_pod()
    pod_id = start_result["pod_id"]
    
    # Record last activity
    await backend_manager.record_activity()
    initial_last_activity = await backend_manager.get_last_activity_time()
    
    # Fast-forward time beyond idle timeout
    with freeze_time(datetime.now() + timedelta(minutes=35)):
        # Act
        await backend_manager.check_idle_timeout()
        
        # Assert
        pod_status = await backend_manager.get_pod_status(pod_id)
        assert pod_status["status"] == "stopped"
        
        # Verify idle shutdown was recorded
        shutdown_events = await mock_runpod.get_shutdown_events()
        assert len(shutdown_events) == 1
        assert shutdown_events[0]["reason"] == "idle_timeout"
        assert shutdown_events[0]["idle_duration_minutes"] >= 30