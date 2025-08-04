# FastAPI + React E-Commerce Application 🛍️

A complete full-stack e-commerce application with modern features including shopping cart, user management, advanced search, image uploads, and order tracking.

## ✨ New Features Implemented

### 🛒 **Shopping Cart System**
- **Add to Cart & Buy Now**: Dual purchase options for each product
- **Cart Management**: Add, remove, update quantities with real-time totals
- **Persistent Cart**: Cart contents saved across sessions
- **Stock Validation**: Prevents overselling with real-time stock checks
- **Sliding Cart UI**: Modern sidebar cart with smooth animations

### 👤 **User Profile Management**
- **Profile Editing**: Update username and email with validation
- **Password Management**: Secure password change with strength requirements
- **Order History**: Detailed purchase history with order tracking
- **Account Settings**: Comprehensive user account management modal

### 🔍 **Advanced Product Search & Filtering**
- **Smart Search**: Search by name, description, or category
- **Price Range Filtering**: Min/max price range controls
- **Advanced Sorting**: Sort by name, price, date, or stock level
- **Category Filtering**: Filter products by category
- **Stock Toggle**: Show/hide out-of-stock items
- **Real-time Results**: Instant search results with result counts

### 📷 **Professional Image Upload System**
- **Drag & Drop Upload**: Modern drag-and-drop interface (Admin only)
- **Image Optimization**: Automatic resizing and compression
- **File Validation**: Type and size restrictions for security
- **Upload Progress**: Real-time upload progress indicators
- **Preview & Management**: Image preview with replace/remove options

### 📦 **Auto Stock Management**
- **Real-time Updates**: Stock automatically decreases on purchases
- **Inventory Tracking**: Live stock counts across the application
- **Stock Validation**: Prevents orders exceeding available inventory
- **Out-of-Stock Handling**: Products disappear when inventory reaches zero

### 📋 **Order Status Tracking**
- **Complete Order Lifecycle**: Pending → Confirmed → Processing → Shipped → Delivered
- **Admin Order Management**: Update status, add tracking numbers and notes
- **Customer Tracking**: Customers can view order status and tracking info
- **Order Statistics**: Admin dashboard with order analytics
- **Status Notifications**: Visual status indicators with color coding

## 🎨 Enhanced UI/UX Features

- **Modern Design**: Professional gradient designs and smooth animations
- **Responsive Layout**: Works perfectly on desktop, tablet, and mobile
- **Real-time Feedback**: Instant notifications and loading states
- **Intuitive Navigation**: Clean, organized interface with role-based views
- **Accessibility**: Screen reader friendly with proper ARIA labels

## 🔧 Technical Stack

- **Backend (FastAPI)**:
  - RESTful API with automatic documentation
  - SQLAlchemy for relational database operations (SQLite by default)
  - JWT authentication with role-based access control
  - File upload handling with image processing (Pillow)
  - Advanced database queries with filtering and sorting
  - Pydantic models for comprehensive data validation

- **Frontend (React + TypeScript)**:
  - Modern React with TypeScript for type safety
  - Axios for API communication with interceptors
  - Responsive UI with CSS-in-JS styling
  - Real-time state management
  - Professional component architecture

## 📁 Enhanced Project Structure

```
fastapi-react-app/
├── backend/
│   ├── main.py                 # FastAPI application entry point
│   ├── requirements.txt        # Python dependencies (includes Pillow)
│   ├── uploads/               # Image upload directory
│   ├── database/
│   │   ├── sql_database.py    # SQLAlchemy setup
│   │   └── mongodb.py         # MongoDB connection
│   ├── models/
│   │   ├── user.py           # User model with cart relationship
│   │   └── item.py           # Item, CartItem, Purchase models with order status
│   ├── schemas/
│   │   ├── user.py           # User schemas with profile management
│   │   ├── item.py           # Item schemas with order status tracking
│   │   └── cart.py           # Shopping cart schemas (NEW)
│   ├── crud/
│   │   ├── user.py           # User operations with profile management
│   │   ├── item.py           # Enhanced item operations with advanced filtering
│   │   └── cart.py           # Shopping cart operations (NEW)
│   └── api/
│       ├── users.py          # User API with profile endpoints
│       ├── items.py          # Enhanced item API with search/filtering/orders
│       ├── cart.py           # Shopping cart API endpoints (NEW)
│       └── upload.py         # Image upload API endpoints (NEW)
├── frontend/
│   ├── src/
│   │   ├── App.tsx           # Main app with profile integration
│   │   └── components/
│   │       ├── Login.tsx     # Authentication component
│   │       ├── AdminPanel.tsx # Enhanced admin panel with order management
│   │       ├── CustomerPanel.tsx # Enhanced customer panel with cart & filters
│   │       ├── ShoppingCart.tsx # Shopping cart component (NEW)
│   │       ├── UserProfile.tsx # User profile management (NEW)
│   │       └── ImageUpload.tsx # Image upload component (NEW)
│   ├── package.json
│   └── ...
├── start-backend.sh          # Backend startup script
├── start-frontend.sh         # Frontend startup script
└── README.md                 # This comprehensive documentation
```

## 🛠️ Setup Instructions

### Prerequisites

- Python 3.8+
- Node.js 14+
- MongoDB (optional - for items functionality)

### Backend Setup

1. **Navigate to the backend directory**:
   ```bash
   cd fastapi-react-app/backend
   ```

2. **Create and activate virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables** (optional):
   Edit `.env` file to customize database URLs and other settings.

### Frontend Setup

1. **Navigate to the frontend directory**:
   ```bash
   cd fastapi-react-app/frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

## 🚀 Running the Application

### Option 1: Using startup scripts (recommended)

1. **Start the backend** (in one terminal):
   ```bash
   cd fastapi-react-app
   ./start-backend.sh
   ```

2. **Start the frontend** (in another terminal):
   ```bash
   cd fastapi-react-app
   ./start-frontend.sh
   ```

### Option 2: Manual startup

**Backend**:
```bash
cd fastapi-react-app/backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend**:
```bash
cd fastapi-react-app/frontend
npm start
```

## 🌐 Accessing the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Alternative API docs**: http://localhost:8000/redoc

## 🔧 Enhanced API Endpoints

### Users & Authentication
- `POST /api/users/` - Create a new user
- `POST /api/users/login` - User login with JWT
- `GET /api/users/me` - Get current user profile
- `PUT /api/users/profile` - Update user profile
- `POST /api/users/change-password` - Change user password
- `GET /api/users/{user_id}` - Get user by ID

### Products & Search
- `GET /api/items/` - Get items with advanced filtering
  - Query params: `search`, `category`, `min_price`, `max_price`, `sort_by`, `sort_order`, `in_stock_only`
- `POST /api/items/` - Create new item (Admin only)
- `PUT /api/items/{item_id}` - Update item (Admin only)
- `DELETE /api/items/{item_id}` - Delete item (Admin only)
- `GET /api/items/{item_id}` - Get item by ID
- `GET /api/items/categories/list` - Get all categories

### Shopping Cart
- `POST /api/cart/add` - Add item to cart
- `GET /api/cart/` - Get cart contents with totals
- `PUT /api/cart/{cart_item_id}` - Update cart item quantity
- `DELETE /api/cart/{cart_item_id}` - Remove item from cart
- `DELETE /api/cart/` - Clear entire cart
- `POST /api/cart/checkout` - Checkout cart (convert to orders)

### Order Management
- `POST /api/items/purchase` - Direct purchase (bypass cart)
- `GET /api/items/purchases/my` - Get user's purchase history
- `GET /api/items/purchases/all` - Get all purchases (Admin only)
- `PUT /api/items/purchases/{purchase_id}/status` - Update order status (Admin only)
- `GET /api/items/orders/stats` - Get order statistics (Admin only)

### Image Upload (Admin Only)
- `POST /api/upload/image` - Upload and optimize image
- `GET /api/upload/image/{filename}` - Serve uploaded images
- `DELETE /api/upload/image/{filename}` - Delete uploaded image
- `GET /api/upload/images` - List all uploaded images

### General
- `GET /` - Welcome message
- `GET /health` - Health check

## 🗄️ Database Configuration

### SQLite (Default)
The application uses SQLite by default for the SQLAlchemy part. The database file `app.db` will be created automatically in the backend directory.

### MongoDB (Optional)
To use MongoDB for items:
1. Install and start MongoDB locally
2. The default connection is `mongodb://localhost:27017`
3. Database name: `fastapi_app`

Update the `.env` file to change these settings.

## 🔒 Environment Variables

Create or modify the `.env` file in the backend directory:

```env
# Database Configuration
DATABASE_URL=sqlite:///./app.db
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=fastapi_app

# App Configuration
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
ALLOWED_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]
```

## 🧪 Feature Testing Guide

### Quick Start Testing:
1. **Access the frontend** at http://localhost:3000
2. **Create an admin user** (set role="admin" in database or via API)
3. **Login as admin** to test admin features
4. **Create products** with image upload
5. **Login as customer** to test shopping features

### 🛒 Shopping Cart Testing:
- Add products to cart using "Add to Cart" button
- Click cart icon in header to view cart
- Modify quantities and remove items
- Complete checkout process

### 👤 Profile Management Testing:
- Click "Profile" button in header
- Update username/email in profile tab
- Change password in password tab
- View order history in orders tab

### 🔍 Search & Filter Testing:
- Use search bar to find products
- Apply category and price filters
- Test different sorting options
- Toggle in-stock only filter

### 📷 Image Upload Testing (Admin):
- Drag and drop images in product creation
- Try different file types and sizes
- Verify image optimization

### 📋 Order Management Testing (Admin):
- View orders in admin panel
- Click "Manage" on orders
- Update order status and add tracking info

## 🛡️ Enhanced Security Features

- **Authentication & Authorization**:
  - JWT token-based authentication
  - Role-based access control (Admin/Customer)
  - Secure password hashing with bcrypt
  - Session management with token expiration

- **Data Security**:
  - Input validation using Pydantic models
  - SQL injection prevention with SQLAlchemy ORM
  - File upload restrictions (type, size, admin-only)
  - XSS protection with input sanitization

- **API Security**:
  - CORS configuration for secure frontend communication
  - Rate limiting ready (easily configurable)
  - Environment-based configuration
  - Secure headers and error handling

## 🚀 Performance Features

- **Frontend Optimizations**:
  - Real-time UI updates without page refreshes
  - Efficient state management
  - Lazy loading and code splitting ready
  - Optimized bundle sizes

- **Backend Optimizations**:
  - Database query optimization with proper indexing
  - Automatic image compression and resizing
  - Efficient filtering and pagination
  - Caching-ready architecture

- **Image Handling**:
  - Automatic image optimization (resize, compress)
  - Support for multiple formats (JPEG, PNG, GIF, WebP)
  - Drag & drop upload with progress indicators
  - File validation and error handling

## 📝 Development Notes

- The backend includes automatic reload during development
- Frontend includes hot reloading for instant updates
- Both databases can be used independently
- API documentation is automatically generated by FastAPI

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
