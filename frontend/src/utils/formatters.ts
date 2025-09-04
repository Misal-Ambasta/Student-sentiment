/**
 * Utility functions for formatting text and data
 */

/**
 * Formats an aspect name by removing underscores and capitalizing each word
 * @param aspectName - The aspect name with underscores (e.g., "instructor_delivery")
 * @returns Formatted aspect name (e.g., "Instructor Delivery")
 */
export const formatAspectName = (aspectName: string): string => {
  if (!aspectName) return '';
  
  return aspectName
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

/**
 * Formats a date string
 * @param dateString - The date string to format
 * @param format - The format to use (optional)
 * @returns Formatted date string
 */
export const formatDate = (dateString: string, format: string = 'PP'): string => {
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString();
  } catch (e) {
    return dateString;
  }
};