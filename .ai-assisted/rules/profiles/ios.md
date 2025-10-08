id: rules.lang.ios
version: 1.0.0
description: iOS/Swift-specific programming guidelines for AI assistants
globs: ["**/*.swift", "**/*.m", "**/*.h", "**/Podfile", "**/*.xcodeproj", "**/*.xcworkspace", "**/Package.swift"]
tags: ["language", "ios"]
---

# iOS/Swift-Specific Guidelines

## Language-Specific Naming Conventions

### Semantic Naming Matrix
| Type | Pattern | Example |
|------|---------|---------|
| Classes/Structs | PascalCase | `UserProfile`, `NetworkManager` |
| Protocols | PascalCase + able/ing | `Codable`, `UITableViewDataSource` |
| Enums | PascalCase | `NetworkError`, `UserRole` |
| Functions | camelCase | `fetchUserData()`, `configureView()` |
| Variables | camelCase | `userName`, `isLoggedIn` |
| Constants | camelCase | `maximumRetryCount`, `defaultTimeout` |
| Type aliases | PascalCase | `CompletionHandler`, `UserID` |
| IBOutlets | camelCase + type suffix | `nameLabel`, `submitButton` |
| IBActions | verb + noun | `submitButtonTapped`, `textFieldDidChange` |

## Code Examples

### Design Patterns

**Simplicity First (YAGNI)**:
```swift
// BAD - Over-engineered
protocol ToolFactoryProtocol {
    func createTool() -> Tool
}

class AbstractToolFactory: ToolFactoryProtocol {
    func createTool() -> Tool {
        return getBuilder().build()
    }
    
    func getBuilder() -> ToolBuilder {
        // Complex builder logic
    }
}

// GOOD - Simple and sufficient
struct Tool {
    let type: ToolType
    
    init(type: ToolType) {
        self.type = type
    }
}
```

**Dependency Injection**:
```swift
// GOOD - Testable with dependency injection
class UserService {
    private let apiClient: APIClientProtocol
    private let cache: CacheProtocol
    
    init(apiClient: APIClientProtocol = APIClient.shared,
         cache: CacheProtocol = UserCache()) {
        self.apiClient = apiClient
        self.cache = cache
    }
    
    func fetchUser(id: Int) async throws -> User {
        if let cached = cache.get(key: "user_\(id)") {
            return cached
        }
        let user = try await apiClient.fetch(endpoint: .user(id))
        cache.set(user, key: "user_\(id)")
        return user
    }
}

// BAD - Hard to test
class UserService {
    func fetchUser(id: Int) async throws -> User {
        // Direct usage without injection
        return try await APIClient.shared.fetch(endpoint: .user(id))
    }
}
```

## File Documentation Template

```swift
//
//  UserService.swift
//  AppName
//
//  Created by Developer Name on MM/DD/YYYY.
//  Copyright © YYYY Company Name. All rights reserved.
//
//  ABOUTME: Primary responsibility of this file
//  ABOUTME: Key patterns: [e.g., Singleton, Observer]
//  DEPENDENCIES: External libraries or frameworks used
//  SECURITY: Any security considerations
//  PERFORMANCE: Known bottlenecks or optimizations
//

import Foundation
import UIKit

/// Main service for user-related operations
/// 
/// Example:
/// ```swift
/// let service = UserService()
/// let user = try await service.fetchUser(id: 123)
/// ```
class UserService {
    // Implementation
}
```

## Swift-Specific Patterns

### Protocol-Oriented Programming
```swift
// Define capabilities through protocols
protocol Identifiable {
    associatedtype ID: Hashable
    var id: ID { get }
}

protocol Timestamped {
    var createdAt: Date { get }
    var updatedAt: Date { get }
}

// Protocol extensions for default implementations
extension Timestamped {
    var age: TimeInterval {
        Date().timeIntervalSince(createdAt)
    }
}

// Combine protocols for complex types
struct User: Identifiable, Timestamped, Codable {
    let id: UUID
    let name: String
    let email: String
    let createdAt: Date
    let updatedAt: Date
}
```

### Result Type and Error Handling
```swift
// Define clear error types
enum NetworkError: LocalizedError {
    case noConnection
    case invalidResponse(statusCode: Int)
    case decodingFailed(Error)
    case unauthorized
    
    var errorDescription: String? {
        switch self {
        case .noConnection:
            return "No internet connection"
        case .invalidResponse(let code):
            return "Server returned invalid response: \(code)"
        case .decodingFailed(let error):
            return "Failed to decode response: \(error.localizedDescription)"
        case .unauthorized:
            return "Authentication required"
        }
    }
}

// Using Result type
func fetchData(completion: @escaping (Result<Data, NetworkError>) -> Void) {
    guard isConnected else {
        completion(.failure(.noConnection))
        return
    }
    
    // Perform network request
    URLSession.shared.dataTask(with: request) { data, response, error in
        if let error = error {
            completion(.failure(.decodingFailed(error)))
            return
        }
        
        guard let data = data else {
            completion(.failure(.invalidResponse(statusCode: 0)))
            return
        }
        
        completion(.success(data))
    }.resume()
}

// Modern async/await approach
func fetchData() async throws -> Data {
    guard isConnected else {
        throw NetworkError.noConnection
    }
    
    let (data, response) = try await URLSession.shared.data(for: request)
    
    guard let httpResponse = response as? HTTPURLResponse,
          (200...299).contains(httpResponse.statusCode) else {
        throw NetworkError.invalidResponse(statusCode: (response as? HTTPURLResponse)?.statusCode ?? 0)
    }
    
    return data
}
```

## SwiftUI Patterns

### View Components
```swift
import SwiftUI

struct UserProfileView: View {
    // MARK: - Properties
    @StateObject private var viewModel: UserProfileViewModel
    @Environment(\.dismiss) private var dismiss
    @State private var isEditing = false
    
    // MARK: - Initialization
    init(userId: String) {
        _viewModel = StateObject(wrappedValue: UserProfileViewModel(userId: userId))
    }
    
    // MARK: - Body
    var body: some View {
        NavigationStack {
            content
                .navigationTitle("Profile")
                .navigationBarTitleDisplayMode(.large)
                .toolbar {
                    ToolbarItem(placement: .navigationBarTrailing) {
                        editButton
                    }
                }
                .alert("Error", isPresented: $viewModel.showError) {
                    Button("OK") { }
                } message: {
                    Text(viewModel.errorMessage)
                }
        }
        .task {
            await viewModel.loadUser()
        }
    }
    
    // MARK: - Views
    private var content: some View {
        ScrollView {
            VStack(spacing: 16) {
                headerSection
                detailsSection
            }
            .padding()
        }
    }
    
    private var headerSection: some View {
        // Implementation
    }
    
    private var detailsSection: some View {
        // Implementation
    }
    
    private var editButton: some View {
        Button("Edit") {
            isEditing.toggle()
        }
    }
}

// MARK: - View Model
@MainActor
class UserProfileViewModel: ObservableObject {
    @Published var user: User?
    @Published var isLoading = false
    @Published var showError = false
    @Published var errorMessage = ""
    
    private let userId: String
    private let userService: UserService
    
    init(userId: String, userService: UserService = .shared) {
        self.userId = userId
        self.userService = userService
    }
    
    func loadUser() async {
        isLoading = true
        defer { isLoading = false }
        
        do {
            user = try await userService.fetchUser(id: userId)
        } catch {
            errorMessage = error.localizedDescription
            showError = true
        }
    }
}
```

## UIKit Patterns

### View Controller Structure
```swift
import UIKit

final class UserProfileViewController: UIViewController {
    
    // MARK: - Properties
    private let viewModel: UserProfileViewModel
    private var cancellables = Set<AnyCancellable>()
    
    // MARK: - UI Elements
    private lazy var tableView: UITableView = {
        let table = UITableView(frame: .zero, style: .insetGrouped)
        table.translatesAutoresizingMaskIntoConstraints = false
        table.delegate = self
        table.dataSource = self
        table.register(UserCell.self, forCellReuseIdentifier: UserCell.reuseIdentifier)
        return table
    }()
    
    private lazy var activityIndicator: UIActivityIndicatorView = {
        let indicator = UIActivityIndicatorView(style: .large)
        indicator.translatesAutoresizingMaskIntoConstraints = false
        indicator.hidesWhenStopped = true
        return indicator
    }()
    
    // MARK: - Initialization
    init(viewModel: UserProfileViewModel) {
        self.viewModel = viewModel
        super.init(nibName: nil, bundle: nil)
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
    
    // MARK: - Lifecycle
    override func viewDidLoad() {
        super.viewDidLoad()
        setupUI()
        setupConstraints()
        bindViewModel()
        viewModel.loadUser()
    }
    
    // MARK: - Setup
    private func setupUI() {
        view.backgroundColor = .systemBackground
        navigationItem.title = "Profile"
        navigationItem.rightBarButtonItem = UIBarButtonItem(
            barButtonSystemItem: .edit,
            target: self,
            action: #selector(editButtonTapped)
        )
        
        view.addSubview(tableView)
        view.addSubview(activityIndicator)
    }
    
    private func setupConstraints() {
        NSLayoutConstraint.activate([
            tableView.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor),
            tableView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            tableView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            tableView.bottomAnchor.constraint(equalTo: view.bottomAnchor),
            
            activityIndicator.centerXAnchor.constraint(equalTo: view.centerXAnchor),
            activityIndicator.centerYAnchor.constraint(equalTo: view.centerYAnchor)
        ])
    }
    
    private func bindViewModel() {
        viewModel.$isLoading
            .receive(on: DispatchQueue.main)
            .sink { [weak self] isLoading in
                if isLoading {
                    self?.activityIndicator.startAnimating()
                } else {
                    self?.activityIndicator.stopAnimating()
                }
            }
            .store(in: &cancellables)
        
        viewModel.$user
            .receive(on: DispatchQueue.main)
            .sink { [weak self] _ in
                self?.tableView.reloadData()
            }
            .store(in: &cancellables)
    }
    
    // MARK: - Actions
    @objc private func editButtonTapped() {
        // Handle edit action
    }
}

// MARK: - UITableViewDataSource
extension UserProfileViewController: UITableViewDataSource {
    func numberOfSections(in tableView: UITableView) -> Int {
        return viewModel.sections.count
    }
    
    func tableView(_ tableView: UITableView, numberOfRowsInSection section: Int) -> Int {
        return viewModel.sections[section].items.count
    }
    
    func tableView(_ tableView: UITableView, cellForRowAt indexPath: IndexPath) -> UITableViewCell {
        // Configure and return cell
    }
}

// MARK: - UITableViewDelegate
extension UserProfileViewController: UITableViewDelegate {
    func tableView(_ tableView: UITableView, didSelectRowAt indexPath: IndexPath) {
        tableView.deselectRow(at: indexPath, animated: true)
        // Handle selection
    }
}
```

## Testing Patterns

### Unit Testing
```swift
import XCTest
@testable import AppName

final class UserServiceTests: XCTestCase {
    
    private var sut: UserService! // System Under Test
    private var mockAPIClient: MockAPIClient!
    private var mockCache: MockCache!
    
    override func setUp() {
        super.setUp()
        mockAPIClient = MockAPIClient()
        mockCache = MockCache()
        sut = UserService(apiClient: mockAPIClient, cache: mockCache)
    }
    
    override func tearDown() {
        sut = nil
        mockAPIClient = nil
        mockCache = nil
        super.tearDown()
    }
    
    // Test naming: test_methodName_condition_expectedResult
    func test_fetchUser_whenUserNotInCache_shouldFetchFromAPI() async throws {
        // Arrange
        let expectedUser = User.mock(id: 1)
        mockCache.getReturnValue = nil
        mockAPIClient.fetchReturnValue = expectedUser
        
        // Act
        let result = try await sut.fetchUser(id: 1)
        
        // Assert
        XCTAssertEqual(result, expectedUser)
        XCTAssertTrue(mockAPIClient.fetchCalled)
        XCTAssertEqual(mockCache.setCalls.count, 1)
    }
    
    func test_fetchUser_whenUserInCache_shouldReturnCachedUser() async throws {
        // Arrange
        let cachedUser = User.mock(id: 1)
        mockCache.getReturnValue = cachedUser
        
        // Act
        let result = try await sut.fetchUser(id: 1)
        
        // Assert
        XCTAssertEqual(result, cachedUser)
        XCTAssertFalse(mockAPIClient.fetchCalled)
    }
    
    func test_fetchUser_whenAPIFails_shouldThrowError() async {
        // Arrange
        mockCache.getReturnValue = nil
        mockAPIClient.shouldThrowError = true
        
        // Act & Assert
        do {
            _ = try await sut.fetchUser(id: 1)
            XCTFail("Expected error to be thrown")
        } catch {
            XCTAssertTrue(error is NetworkError)
        }
    }
}

// Mock objects
class MockAPIClient: APIClientProtocol {
    var fetchCalled = false
    var fetchReturnValue: User?
    var shouldThrowError = false
    
    func fetch<T>(endpoint: Endpoint) async throws -> T where T: Decodable {
        fetchCalled = true
        if shouldThrowError {
            throw NetworkError.noConnection
        }
        guard let value = fetchReturnValue as? T else {
            throw NetworkError.invalidResponse(statusCode: 500)
        }
        return value
    }
}
```

## Memory Management

### Avoiding Retain Cycles
```swift
class ViewController: UIViewController {
    private var timer: Timer?
    private var networkTask: URLSessionTask?
    
    override func viewDidLoad() {
        super.viewDidLoad()
        
        // GOOD - Weak self in closures
        timer = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { [weak self] _ in
            self?.updateUI()
        }
        
        // GOOD - Weak/unowned references
        networkTask = URLSession.shared.dataTask(with: url) { [weak self] data, response, error in
            guard let self = self else { return }
            self.handleResponse(data: data)
        }
        
        // BAD - Strong reference cycle
        timer = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { _ in
            self.updateUI() // Strong reference to self
        }
    }
    
    deinit {
        timer?.invalidate()
        networkTask?.cancel()
    }
}

// Delegate pattern with weak references
protocol DataManagerDelegate: AnyObject {
    func dataManagerDidUpdate(_ manager: DataManager)
}

class DataManager {
    weak var delegate: DataManagerDelegate?
    
    func performUpdate() {
        // Update logic
        delegate?.dataManagerDidUpdate(self)
    }
}
```

## Performance Optimization

### Efficient Collection Operations
```swift
// Use lazy operations for large collections
let processedData = largeArray
    .lazy
    .filter { $0.isValid }
    .map { transform($0) }
    .prefix(100)

// Efficient string concatenation
let components = ["Hello", "World", "from", "Swift"]
let result = components.joined(separator: " ") // Better than multiple + operations

// Use value types when possible
struct User { // Struct (value type) is more efficient than class for simple data
    let id: Int
    let name: String
}

// Dispatch heavy work to background queues
func processLargeDataset() {
    DispatchQueue.global(qos: .userInitiated).async {
        let processed = self.heavyComputation()
        
        DispatchQueue.main.async {
            self.updateUI(with: processed)
        }
    }
}
```

### Image and Asset Management
```swift
// Efficient image loading
extension UIImageView {
    func loadImage(from url: URL) {
        // Cancel previous task if exists
        URLSession.shared.dataTask(with: url) { [weak self] data, _, error in
            guard let data = data,
                  let image = UIImage(data: data) else { return }
            
            DispatchQueue.main.async {
                self?.image = image
            }
        }.resume()
    }
}

// Asset catalog usage
let icon = UIImage(named: "app-icon") // Automatically handles @2x, @3x
let color = UIColor(named: "brandColor") // Supports dark mode
```

## Security Best Practices

### Keychain Storage
```swift
import Security

enum KeychainHelper {
    static func save(key: String, data: Data) -> Bool {
        let query: [CFString: Any] = [
            kSecClass: kSecClassGenericPassword,
            kSecAttrAccount: key,
            kSecValueData: data,
            kSecAttrAccessible: kSecAttrAccessibleWhenUnlockedThisDeviceOnly
        ]
        
        SecItemDelete(query as CFDictionary) // Delete existing
        let status = SecItemAdd(query as CFDictionary, nil)
        return status == errSecSuccess
    }
    
    static func load(key: String) -> Data? {
        let query: [CFString: Any] = [
            kSecClass: kSecClassGenericPassword,
            kSecAttrAccount: key,
            kSecReturnData: true,
            kSecMatchLimit: kSecMatchLimitOne
        ]
        
        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)
        
        guard status == errSecSuccess,
              let data = result as? Data else { return nil }
        return data
    }
}

// Biometric authentication
import LocalAuthentication

func authenticateWithBiometrics(completion: @escaping (Bool) -> Void) {
    let context = LAContext()
    var error: NSError?
    
    guard context.canEvaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, error: &error) else {
        completion(false)
        return
    }
    
    context.evaluatePolicy(.deviceOwnerAuthenticationWithBiometrics,
                          localizedReason: "Authenticate to access your account") { success, error in
        DispatchQueue.main.async {
            completion(success)
        }
    }
}
```

## Code Generation Patterns

When generating iOS/Swift code, always:
1. Use modern Swift syntax (async/await, property wrappers)
2. Include proper access control (private, internal, public)
3. Add MARK comments for organization
4. Handle optionals safely (guard, if let, nil coalescing)
5. Follow MVC/MVVM/MVP architecture consistently
6. Write unit tests using XCTest
7. Use dependency injection for testability
8. Consider memory management (weak/unowned references)
