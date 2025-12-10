/**
 * Utility for merging Tailwind CSS classes
 * Uses clsx and tailwind-merge to handle conflicting classes
 */

import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

/**
 * Merge multiple class names, handling Tailwind conflicts
 * @param inputs - Class names to merge
 * @returns Merged class string
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
