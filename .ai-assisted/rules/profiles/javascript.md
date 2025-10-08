id: rules.lang.javascript
version: 1.0.0
description: JavaScript-specific programming guidelines for AI assistants
globs: ["**/*.js", "**/*.jsx", "**/*.mjs", "**/package.json", "**/*.json"]
tags: ["language", "javascript"]
---

# JavaScript-Specific Guidelines

## Language-Specific Naming Conventions

### Semantic Naming Matrix
| Type | Pattern | Example |
|------|---------|---------|
| Classes | PascalCase | `DataProcessor`, `AuthenticationService` |
| Functions | camelCase | `validateInput()`, `processRequest()` |
| Variables | camelCase | `userCount`, `isAuthenticated` |
| Constants | SCREAMING_SNAKE | `MAX_RETRY_ATTEMPTS`, `API_BASE_URL` |
| Private methods | Leading underscore | `_internalHelper()` |
| React components | PascalCase | `UserProfile`, `NavigationBar` |
| Hooks | camelCase with 'use' | `useAuth()`, `useLocalStorage()` |
| Event handlers | 'handle' prefix | `handleClick`, `handleSubmit` |

## Code Examples

### Design Patterns

**Simplicity First (YAGNI)**:
```javascript
// BAD - Over-engineered
class AbstractToolFactory {
  constructor(config) {
    this.config = config;
  }
  
  createTool() {
    return this.getBuilder().build();
  }
  
  getBuilder() {
    // Complex builder logic
  }
}

// GOOD - Simple and sufficient
function createTool(toolType) {
  return new Tool(toolType);
}
```

**Module Pattern**:
```javascript
// ES6 Module Pattern
// userService.js
class UserService {
  constructor(apiClient) {
    this.apiClient = apiClient;
  }
  
  async getUser(id) {
    try {
      return await this.apiClient.get(`/users/${id}`);
    } catch (error) {
      throw new Error(`Failed to fetch user ${id}: ${error.message}`);
    }
  }
}

export default UserService;

// Singleton pattern when needed
let instance = null;

export class ConfigManager {
  constructor() {
    if (instance) {
      return instance;
    }
    this.config = {};
    instance = this;
  }
}
```

## File Documentation Template

```javascript
/**
 * @fileoverview Primary responsibility of this module
 * @module ModuleName
 * 
 * ABOUTME: Key patterns used in this module
 * DEPENDENCIES: External libraries used
 * SECURITY: Any security considerations
 * PERFORMANCE: Known bottlenecks or optimizations
 * 
 * @example
 * import { mainFunction } from './module';
 * const result = mainFunction(param);
 * console.log(result);
 */

// Imports grouped and ordered
// Node built-ins
import fs from 'fs';
import path from 'path';

// External dependencies
import express from 'express';
import lodash from 'lodash';

// Internal dependencies
import { validateInput } from './utils/validation';
import { API_BASE_URL, MAX_RETRIES } from './constants';
```

## JSDoc and Type Documentation

```javascript
/**
 * Process user data with optional filtering
 * @param {Array<User>} users - List of user objects
 * @param {Object} options - Processing options
 * @param {boolean} [options.filterInactive=true] - Whether to filter inactive users
 * @param {string} [options.sortBy='name'] - Field to sort by
 * @returns {Map<number, User>} Map of user IDs to User objects
 * @throws {Error} Throws if users array is empty
 */
function processUsers(users, options = {}) {
  const { filterInactive = true, sortBy = 'name' } = options;
  
  if (!users || users.length === 0) {
    throw new Error('Users array cannot be empty');
  }
  
  const processed = filterInactive 
    ? users.filter(user => user.isActive)
    : users;
    
  return new Map(processed.map(user => [user.id, user]));
}

/**
 * @typedef {Object} User
 * @property {number} id - User ID
 * @property {string} name - User name
 * @property {string} email - User email
 * @property {boolean} isActive - Whether user is active
 * @property {Array<string>} roles - User roles
 */

/**
 * @class
 * @implements {EventEmitter}
 */
class UserManager {
  /**
   * Create a UserManager instance
   * @param {UserRepository} repository - User repository instance
   */
  constructor(repository) {
    this.repository = repository;
  }
}
```

## Error Handling

### Error Response Pattern
```javascript
class ErrorResponse extends Error {
  constructor(errorCode, message, details = {}, statusCode = 500) {
    super(message);
    this.name = 'ErrorResponse';
    this.errorCode = errorCode;
    this.details = details;
    this.statusCode = statusCode;
    this.timestamp = new Date().toISOString();
    this.requestId = null; // Set by middleware
  }
  
  toJSON() {
    return {
      error_code: this.errorCode,
      message: this.message,
      details: this.details,
      timestamp: this.timestamp,
      request_id: this.requestId
    };
  }
}

// Custom error types
class ValidationError extends ErrorResponse {
  constructor(field, value, message) {
    super(
      'VALIDATION_ERROR',
      message || `Invalid value for field: ${field}`,
      { field, value },
      400
    );
  }
}

// Usage
try {
  const result = await riskyOperation();
} catch (error) {
  if (error instanceof ValidationError) {
    logger.error('Validation failed:', error.toJSON());
    return res.status(error.statusCode).json(error.toJSON());
  }
  
  // Unexpected error
  const unexpectedError = new ErrorResponse(
    'INTERNAL_ERROR',
    'An unexpected error occurred',
    { originalError: error.message }
  );
  logger.error('Unexpected error:', unexpectedError.toJSON());
  return res.status(500).json(unexpectedError.toJSON());
}
```

### Async Error Handling
```javascript
// Async wrapper for Express routes
const asyncHandler = (fn) => (req, res, next) => {
  Promise.resolve(fn(req, res, next)).catch(next);
};

// Usage in Express
router.get('/users/:id', asyncHandler(async (req, res) => {
  const user = await userService.getUser(req.params.id);
  res.json(user);
}));

// Promise error handling
async function fetchWithRetry(url, maxRetries = 3) {
  let lastError;
  
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      lastError = error;
      logger.warn(`Attempt ${i + 1} failed: ${error.message}`);
      
      if (i < maxRetries - 1) {
        await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, i)));
      }
    }
  }
  
  throw new Error(`Failed after ${maxRetries} attempts: ${lastError.message}`);
}
```

## Testing Patterns

### Test Structure Template (Jest/Mocha)
```javascript
describe('UserService', () => {
  let userService;
  let mockRepository;
  
  beforeEach(() => {
    // Arrange - Setup mocks and instances
    mockRepository = {
      findById: jest.fn(),
      save: jest.fn(),
      delete: jest.fn()
    };
    userService = new UserService(mockRepository);
  });
  
  afterEach(() => {
    jest.clearAllMocks();
  });
  
  describe('getUser', () => {
    it('should throw NotFoundError when user does not exist', async () => {
      // Arrange
      const userId = 999;
      mockRepository.findById.mockResolvedValue(null);
      
      // Act & Assert
      await expect(userService.getUser(userId))
        .rejects
        .toThrow(new NotFoundError(`User ${userId} not found`));
      
      expect(mockRepository.findById).toHaveBeenCalledWith(userId);
      expect(mockRepository.findById).toHaveBeenCalledTimes(1);
    });
    
    it('should return user when found', async () => {
      // Arrange
      const expectedUser = { id: 1, name: 'Test User' };
      mockRepository.findById.mockResolvedValue(expectedUser);
      
      // Act
      const result = await userService.getUser(1);
      
      // Assert
      expect(result).toEqual(expectedUser);
      expect(mockRepository.findById).toHaveBeenCalledWith(1);
    });
  });
  
  describe('email validation', () => {
    test.each([
      ['', false],
      ['invalid', false],
      ['user@example.com', true],
      ['user+tag@example.co.uk', true],
    ])('isValidEmail("%s") should return %s', (input, expected) => {
      expect(userService.isValidEmail(input)).toBe(expected);
    });
  });
});
```

## Modern JavaScript Patterns

### Destructuring and Spread
```javascript
// Object destructuring with defaults
function processOptions({ 
  timeout = 5000, 
  retries = 3,
  ...otherOptions 
} = {}) {
  // Use timeout, retries, and otherOptions
}

// Array destructuring
const [first, second, ...rest] = array;

// Nested destructuring
const { 
  user: { 
    name, 
    address: { city } 
  } 
} = response;

// Spread for immutable updates
const updatedUser = {
  ...user,
  name: 'New Name',
  roles: [...user.roles, 'admin']
};
```

### Optional Chaining and Nullish Coalescing
```javascript
// Optional chaining
const city = user?.address?.city ?? 'Unknown';

// Nullish coalescing for defaults
const port = process.env.PORT ?? 3000;
const timeout = config.timeout ?? 5000;

// Combined with destructuring
const { name = 'Anonymous' } = user ?? {};
```

### Async/Await Patterns
```javascript
// Parallel execution
async function fetchAllData(ids) {
  const promises = ids.map(id => fetchData(id));
  return Promise.all(promises);
}

// Sequential execution when needed
async function processSequentially(items) {
  const results = [];
  for (const item of items) {
    const result = await processItem(item);
    results.push(result);
  }
  return results;
}

// Error handling with multiple async operations
async function complexOperation() {
  const [userResult, configResult] = await Promise.allSettled([
    fetchUser(),
    fetchConfig()
  ]);
  
  if (userResult.status === 'rejected') {
    throw new Error(`User fetch failed: ${userResult.reason}`);
  }
  
  if (configResult.status === 'rejected') {
    logger.warn('Using default config due to fetch failure');
    return { user: userResult.value, config: defaultConfig };
  }
  
  return { user: userResult.value, config: configResult.value };
}
```

## Performance Optimization Patterns

### Memoization
```javascript
// Simple memoization
const memoize = (fn) => {
  const cache = new Map();
  return (...args) => {
    const key = JSON.stringify(args);
    if (cache.has(key)) {
      return cache.get(key);
    }
    const result = fn(...args);
    cache.set(key, result);
    return result;
  };
};

const expensiveComputation = memoize((n) => {
  // Complex calculation
  return result;
});

// With TTL (Time To Live)
const memoizeWithTTL = (fn, ttl = 60000) => {
  const cache = new Map();
  
  return (...args) => {
    const key = JSON.stringify(args);
    const cached = cache.get(key);
    
    if (cached && Date.now() - cached.timestamp < ttl) {
      return cached.value;
    }
    
    const result = fn(...args);
    cache.set(key, { value: result, timestamp: Date.now() });
    return result;
  };
};
```

### Debouncing and Throttling
```javascript
// Debounce implementation
function debounce(func, delay) {
  let timeoutId;
  return function(...args) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func.apply(this, args), delay);
  };
}

// Throttle implementation
function throttle(func, limit) {
  let inThrottle;
  return function(...args) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
}

// Usage
const debouncedSearch = debounce(searchAPI, 300);
const throttledScroll = throttle(handleScroll, 100);
```

## Security Best Practices

### Input Validation and Sanitization
```javascript
import validator from 'validator';
import DOMPurify from 'isomorphic-dompurify';

// Input validation
function validateUserInput(input) {
  const errors = [];
  
  if (!validator.isEmail(input.email)) {
    errors.push({ field: 'email', message: 'Invalid email format' });
  }
  
  if (!validator.isLength(input.password, { min: 8 })) {
    errors.push({ field: 'password', message: 'Password must be at least 8 characters' });
  }
  
  // XSS prevention
  const sanitizedBio = DOMPurify.sanitize(input.bio);
  
  if (errors.length > 0) {
    throw new ValidationError('Input validation failed', errors);
  }
  
  return { ...input, bio: sanitizedBio };
}

// SQL injection prevention (using parameterized queries)
async function getUser(userId) {
  // Using a query builder (e.g., Knex.js)
  return await knex('users')
    .where('id', userId)  // Automatically parameterized
    .first();
}
```

### Secure Token Generation
```javascript
import crypto from 'crypto';

// Generate secure random token
function generateSecureToken(length = 32) {
  return crypto.randomBytes(length).toString('hex');
}

// Generate CSRF token
function generateCSRFToken(sessionId) {
  const hash = crypto.createHash('sha256');
  hash.update(sessionId + process.env.CSRF_SECRET);
  return hash.digest('hex');
}

// JWT handling
import jwt from 'jsonwebtoken';

function generateJWT(payload) {
  return jwt.sign(payload, process.env.JWT_SECRET, {
    expiresIn: '1h',
    issuer: 'your-app',
    audience: 'your-app-users'
  });
}

function verifyJWT(token) {
  try {
    return jwt.verify(token, process.env.JWT_SECRET, {
      issuer: 'your-app',
      audience: 'your-app-users'
    });
  } catch (error) {
    throw new UnauthorizedError('Invalid token');
  }
}
```

## Logging Standards

```javascript
// Winston configuration
import winston from 'winston';

const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.simple()
      )
    }),
    new winston.transports.File({
      filename: 'error.log',
      level: 'error',
      maxsize: 5242880, // 5MB
      maxFiles: 5
    }),
    new winston.transports.File({
      filename: 'combined.log',
      maxsize: 5242880, // 5MB
      maxFiles: 5
    })
  ]
});

// Structured logging
logger.info('User action completed', {
  userId: user.id,
  action: 'login',
  ipAddress: req.ip,
  userAgent: req.get('user-agent'),
  duration: Date.now() - startTime
});

// Log levels
logger.debug('Detailed diagnostic info');
logger.info('General informational messages');
logger.warn('Something unexpected but handled');
logger.error('Error that should be investigated', { error });
logger.fatal('System-breaking error');
```

## Code Generation Patterns

When generating JavaScript code, always:
1. Use modern ES6+ syntax (const/let, arrow functions, template literals)
2. Include JSDoc comments for functions and classes
3. Add error handling with try-catch for async operations
4. Use strict mode implicitly (modules) or explicitly ('use strict')
5. Provide usage examples
6. Write corresponding test cases using Jest or Mocha

### Module Organization
```javascript
// userService.js
export class UserService {
  // Implementation
}

export function validateUser(user) {
  // Implementation
}

export const USER_ROLES = {
  ADMIN: 'admin',
  USER: 'user'
};

// Default export for main functionality
export default UserService;

// Import in another file
import UserService, { validateUser, USER_ROLES } from './userService';
```
