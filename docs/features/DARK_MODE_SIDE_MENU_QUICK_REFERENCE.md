# 🌙 Dark Mode & Side Menu - Quick Reference Guide

## 🚀 Quick Start

### **Dark Mode Toggle**
- **Location**: Available in all portal headers
- **Usage**: Click the theme toggle button to switch between light/dark modes
- **Persistence**: Theme selection is saved and restored on page reload

### **Side Menu Navigation**
- **Location**: Admin (`/admin/`) and Manager (`/manager/`) dashboards
- **Usage**: Click the hamburger menu (☰) in the header
- **Features**: Quick access to View Site, Change Password, Log Out, and Dark Mode toggle

## 📱 Mobile Usage

### **Touch Interface**
- **Side Menu**: Swipe or tap hamburger menu to open
- **Close Menu**: Tap outside the menu or use the X button
- **Theme Toggle**: Tap the theme button in header or side menu

### **Responsive Design**
- **All screen sizes** supported (mobile, tablet, desktop)
- **Touch-friendly** buttons and navigation
- **Smooth animations** optimized for mobile devices

## 🎨 Visual Features

### **Dark Mode Styling**
- **Professional color scheme** with proper contrast ratios
- **Consistent theming** across all portals
- **Smooth transitions** between light and dark modes
- **SVG icons** for professional appearance

### **Side Menu Design**
- **Glass-morphism effects** for modern appearance
- **User profile display** with name and role
- **Smooth slide-out animation** from the right
- **Professional styling** with hover effects

## 🔧 Technical Details

### **Browser Support**
- **Chrome**: Full support
- **Firefox**: Full support
- **Safari**: Full support
- **Edge**: Full support

### **Accessibility**
- **ARIA attributes** for screen readers
- **Keyboard navigation** support
- **High contrast** color schemes
- **Focus indicators** for navigation

## 🚨 Troubleshooting

### **Common Issues**

#### **Dark Mode Not Working**
- **Check**: Browser console for JavaScript errors
- **Solution**: Refresh the page and try again
- **Fallback**: Theme toggle should work in side menu

#### **Side Menu Not Opening**
- **Check**: JavaScript is enabled in browser
- **Solution**: Refresh the page and try again
- **Alternative**: Use direct navigation links

#### **Mobile Issues**
- **Check**: Touch events are working
- **Solution**: Ensure proper touch support in browser
- **Fallback**: Use desktop version if needed

### **Browser Console Commands**
```javascript
// Check if dark mode is active
document.documentElement.getAttribute('data-theme')

// Toggle dark mode manually
document.getElementById('theme-toggle').click()

// Check if side menu is open
document.getElementById('side-menu').style.right
```

## 📊 Feature Matrix

| **Portal** | **Dark Mode** | **Side Menu** | **Mobile Support** |
|------------|---------------|---------------|-------------------|
| Staff Portal | ✅ | ❌ | ✅ |
| Admin Dashboard | ✅ | ✅ | ✅ |
| Manager Dashboard | ✅ | ✅ | ✅ |
| Portal Home | ✅ | ❌ | ✅ |

## 🎯 Best Practices

### **For Users**
1. **Use dark mode** in low-light environments
2. **Access side menu** for quick navigation
3. **Test on mobile** for optimal experience
4. **Report issues** if functionality doesn't work

### **For Developers**
1. **Follow CSS custom properties** for theming
2. **Include ARIA attributes** for accessibility
3. **Test on multiple devices** before deployment
4. **Maintain consistent styling** across portals

## 🔗 Related Documentation

- [`DARK_MODE_SIDE_MENU_IMPROVEMENTS_2025-09-10.md`](./DARK_MODE_SIDE_MENU_IMPROVEMENTS_2025-09-10.md) - Complete implementation details
- [`UI_UX_IMPROVEMENTS.md`](./UI_UX_IMPROVEMENTS.md) - Overall UI/UX improvements
- [`DARK_MODE_SIDE_MENU_IMPLEMENTATION_REPORT_2025-09-10.md`](../reports/DARK_MODE_SIDE_MENU_IMPLEMENTATION_REPORT_2025-09-10.md) - Implementation report

---

**Last Updated**: September 10, 2025  
**Status**: ✅ Production Ready  
**Version**: 1.0.0
