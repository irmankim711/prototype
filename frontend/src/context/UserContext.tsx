import {
  createContext,
  useState,
  useEffect,
  useContext,
  useCallback,
} from "react";
import type { ReactNode } from "react";
import { AuthContext } from "./AuthContext";
import { updateUserProfile } from "../services/api";
import type {
  User as ApiUser,
  UpdateUserProfileResponse,
} from "../services/api";

// Type for AuthContext User (from JWT)
interface AuthUser {
  id: number;
  email: string;
  username: string;
  first_name?: string;
  last_name?: string;
  full_name?: string;
  role: string;
  organization_id?: number;
  avatar_url?: string;
  is_active: boolean;
}

// Enhanced user data interface that combines all user information
export interface EnhancedUser extends ApiUser {
  // Display helpers
  display_name: string;
  initials: string;
  avatar_display_url: string;
  // Status information
  is_online: boolean;
  last_seen?: string;
}

interface UserContextType {
  // User data
  currentUser: EnhancedUser | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  refreshUserData: () => Promise<void>;
  updateUserData: (
    userData: Partial<ApiUser>
  ) => Promise<UpdateUserProfileResponse>;
  getUserDisplayName: () => string;
  getUserInitials: () => string;
  getUserAvatarUrl: () => string;

  // Profile management
  isProfileComplete: boolean;
  profileCompletionPercentage: number;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

// Helper functions for user data processing
const generateInitials = (
  firstName?: string,
  lastName?: string,
  email?: string
): string => {
  if (firstName && lastName) {
    return `${firstName.charAt(0)}${lastName.charAt(0)}`.toUpperCase();
  }
  if (firstName) {
    return firstName.substring(0, 2).toUpperCase();
  }
  if (lastName) {
    return lastName.substring(0, 2).toUpperCase();
  }
  if (email) {
    return email.substring(0, 2).toUpperCase();
  }
  return "U";
};

const generateDisplayName = (user: ApiUser): string => {
  if (user.first_name && user.last_name) {
    return `${user.first_name} ${user.last_name}`;
  }
  if (user.first_name) {
    return user.first_name;
  }
  if (user.last_name) {
    return user.last_name;
  }
  if (user.username) {
    return user.username;
  }
  return user.email || "Unknown User";
};

const generateAvatarUrl = (user: ApiUser): string => {
  if (user.avatar_url) {
    return user.avatar_url;
  }

  const initials = generateInitials(
    user.first_name,
    user.last_name,
    user.email
  );

  // Generate a UI-avatars.com URL with consistent styling
  const backgroundColor = "6366f1"; // Primary blue
  const textColor = "ffffff";

  return `https://ui-avatars.com/api/?name=${encodeURIComponent(
    initials
  )}&background=${backgroundColor}&color=${textColor}&size=128&bold=true`;
};

const calculateProfileCompletion = (user: ApiUser): number => {
  const fields = [
    user.first_name,
    user.last_name,
    user.username,
    user.email,
    user.phone,
    user.company,
    user.job_title,
    user.bio,
    user.avatar_url,
  ];

  const completedFields = fields.filter(
    (field) => field && field.trim().length > 0
  );
  return Math.round((completedFields.length / fields.length) * 100);
};

const enhanceUserData = (user: ApiUser): EnhancedUser => {
  const display_name = generateDisplayName(user);
  const initials = generateInitials(
    user.first_name,
    user.last_name,
    user.email
  );
  const avatar_display_url = generateAvatarUrl(user);

  return {
    ...user,
    display_name,
    initials,
    avatar_display_url,
    is_online: true, // This could be enhanced with real-time status
    last_seen: new Date().toISOString(),
  };
};

export function UserProvider({ children }: { children: ReactNode }) {
  const {
    user: authUser,
    userProfile,
    isLoading: authLoading,
    refreshUserProfile,
  } = useContext(AuthContext);

  const [currentUser, setCurrentUser] = useState<EnhancedUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Combine auth user and profile data
  const combineUserData = useCallback(
    (
      authUser: AuthUser | null,
      userProfile: ApiUser | null
    ): ApiUser | null => {
      if (!authUser && !userProfile) return null;

      // Merge data, preferring profile data when available
      return {
        id: userProfile?.id || String(authUser?.id || ""),
        email: userProfile?.email || authUser?.email || "",
        username: userProfile?.username || authUser?.username,
        first_name: userProfile?.first_name || authUser?.first_name,
        last_name: userProfile?.last_name || authUser?.last_name,
        full_name: userProfile?.full_name || authUser?.full_name,
        role: userProfile?.role || authUser?.role || "",
        phone: userProfile?.phone || "",
        company: userProfile?.company || "",
        job_title: userProfile?.job_title || "",
        bio: userProfile?.bio || "",
        avatar_url: userProfile?.avatar_url || authUser?.avatar_url,
        timezone: userProfile?.timezone || "UTC",
        language: userProfile?.language || "en",
        theme: userProfile?.theme || "light",
        email_notifications: userProfile?.email_notifications ?? true,
        push_notifications: userProfile?.push_notifications ?? false,
        is_active: userProfile?.is_active ?? authUser?.is_active ?? true,
        created_at: userProfile?.created_at || new Date().toISOString(),
        updated_at: userProfile?.updated_at || new Date().toISOString(),
        last_login: userProfile?.last_login,
        permissions: userProfile?.permissions || [],
      };
    },
    []
  );

  // Update current user when auth data changes
  useEffect(() => {
    const updateCurrentUser = async () => {
      try {
        setIsLoading(true);
        setError(null);

        const combinedUser = combineUserData(
          authUser as AuthUser,
          userProfile ? (userProfile as unknown as ApiUser) : null
        );

        if (combinedUser) {
          const enhancedUser = enhanceUserData(combinedUser);
          setCurrentUser(enhancedUser);
        } else {
          setCurrentUser(null);
        }
      } catch (err) {
        console.error("Error updating current user:", err);
        setError("Failed to load user data");
      } finally {
        setIsLoading(false);
      }
    };

    if (!authLoading) {
      updateCurrentUser();
    }
  }, [authUser, userProfile, authLoading, combineUserData]);

  // Refresh user data from API
  const refreshUserData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Trigger refresh of user profile in AuthContext
      if (refreshUserProfile) {
        await refreshUserProfile();
      }

      // The useEffect above will handle updating currentUser
    } catch (err) {
      console.error("Error refreshing user data:", err);
      setError("Failed to refresh user data");
    } finally {
      setIsLoading(false);
    }
  }, [refreshUserProfile]);

  // Update user data and sync across components
  const updateUserData = useCallback(
    async (userData: Partial<ApiUser>): Promise<UpdateUserProfileResponse> => {
      try {
        setIsLoading(true);
        setError(null);

        // Update via API
        const response = await updateUserProfile(userData);

        // Refresh user data to ensure consistency
        await refreshUserData();

        return response;
      } catch (err) {
        console.error("Error updating user data:", err);
        setError("Failed to update user data");
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [refreshUserData]
  );

  // Helper functions
  const getUserDisplayName = useCallback((): string => {
    return currentUser?.display_name || "Unknown User";
  }, [currentUser]);

  const getUserInitials = useCallback((): string => {
    return currentUser?.initials || "U";
  }, [currentUser]);

  const getUserAvatarUrl = useCallback((): string => {
    return (
      currentUser?.avatar_display_url ||
      `https://ui-avatars.com/api/?name=U&background=6366f1&color=ffffff&size=128&bold=true`
    );
  }, [currentUser]);

  // Profile completion calculations
  const profileCompletionPercentage = currentUser
    ? calculateProfileCompletion(currentUser)
    : 0;
  const isProfileComplete = profileCompletionPercentage >= 80;

  const contextValue: UserContextType = {
    currentUser,
    isLoading: isLoading || authLoading,
    error,
    refreshUserData,
    updateUserData,
    getUserDisplayName,
    getUserInitials,
    getUserAvatarUrl,
    isProfileComplete,
    profileCompletionPercentage,
  };

  return (
    <UserContext.Provider value={contextValue}>{children}</UserContext.Provider>
  );
}

// Export the context for direct usage if needed
export { UserContext };
