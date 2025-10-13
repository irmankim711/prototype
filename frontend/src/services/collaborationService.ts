/**
 * Collaboration Service
 * Handles sharing, commenting, and real-time collaboration on charts and reports
 */

import type { ChartData, ChartConfig } from '../components/NextGenReportBuilder/types';

export interface CollaborationUser {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  role: 'owner' | 'editor' | 'viewer' | 'commenter';
  permissions: string[];
  lastActive: Date;
}

export interface CollaborationSession {
  id: string;
  chartId: string;
  title: string;
  description?: string;
  owner: CollaborationUser;
  participants: CollaborationUser[];
  status: 'active' | 'paused' | 'ended';
  createdAt: Date;
  updatedAt: Date;
  settings: CollaborationSettings;
}

export interface CollaborationSettings {
  allowEditing: boolean;
  allowCommenting: boolean;
  allowSharing: boolean;
  requireApproval: boolean;
  autoSave: boolean;
  versionControl: boolean;
  maxParticipants: number;
  sessionTimeout: number;
}

export interface Comment {
  id: string;
  chartId: string;
  author: CollaborationUser;
  content: string;
  position?: {
    x: number;
    y: number;
    element?: string;
  };
  replies: Comment[];
  createdAt: Date;
  updatedAt: Date;
  status: 'active' | 'resolved' | 'archived';
  tags: string[];
}

export interface ShareLink {
  id: string;
  chartId: string;
  url: string;
  password?: string;
  expiresAt?: Date;
  maxViews?: number;
  currentViews: number;
  permissions: string[];
  createdAt: Date;
  createdBy: CollaborationUser;
}

export interface VersionHistory {
  id: string;
  chartId: string;
  version: number;
  description: string;
  changes: string[];
  chartData: ChartData;
  chartConfig: ChartConfig;
  createdBy: CollaborationUser;
  createdAt: Date;
  tags: string[];
}

export interface CollaborationActivity {
  id: string;
  chartId: string;
  type: 'edit' | 'comment' | 'share' | 'version' | 'access' | 'permission';
  user: CollaborationUser;
  description: string;
  metadata?: Record<string, any>;
  timestamp: Date;
}

export interface CollaborationInvite {
  id: string;
  chartId: string;
  email: string;
  role: 'editor' | 'viewer' | 'commenter';
  permissions: string[];
  message?: string;
  expiresAt: Date;
  status: 'pending' | 'accepted' | 'declined' | 'expired';
  createdAt: Date;
  createdBy: CollaborationUser;
}

class CollaborationService {
  private sessions: Map<string, CollaborationSession> = new Map();
  private comments: Map<string, Comment[]> = new Map();
  private shareLinks: Map<string, ShareLink> = new Map();
  private versionHistory: Map<string, VersionHistory[]> = new Map();
  private activities: Map<string, CollaborationActivity[]> = new Map();
  private invites: Map<string, CollaborationInvite[]> = new Map();
  private currentUser: CollaborationUser | null = null;

  constructor() {
    this.initializeMockData();
  }

  /**
   * Initialize mock data for development
   */
  private initializeMockData(): void {
    // Mock current user
    this.currentUser = {
      id: 'user-1',
      name: 'John Doe',
      email: 'john.doe@example.com',
      avatar: '/avatars/john-doe.jpg',
      role: 'owner',
      permissions: ['read', 'write', 'share', 'comment', 'manage'],
      lastActive: new Date()
    };

    // Mock collaboration session
    const mockSession: CollaborationSession = {
      id: 'session-1',
      chartId: 'chart-1',
      title: 'Q4 Sales Analysis',
      description: 'Collaborative analysis of Q4 sales performance',
      owner: this.currentUser,
      participants: [
        this.currentUser,
        {
          id: 'user-2',
          name: 'Jane Smith',
          email: 'jane.smith@example.com',
          avatar: '/avatars/jane-smith.jpg',
          role: 'editor',
          permissions: ['read', 'write', 'comment'],
          lastActive: new Date()
        }
      ],
      status: 'active',
      createdAt: new Date(),
      updatedAt: new Date(),
      settings: {
        allowEditing: true,
        allowCommenting: true,
        allowSharing: true,
        requireApproval: false,
        autoSave: true,
        versionControl: true,
        maxParticipants: 10,
        sessionTimeout: 3600000 // 1 hour
      }
    };

    this.sessions.set(mockSession.id, mockSession);
  }

  /**
   * Get current user
   */
  getCurrentUser(): CollaborationUser | null {
    return this.currentUser;
  }

  /**
   * Create new collaboration session
   */
  createCollaborationSession(
    chartId: string,
    title: string,
    description?: string,
    settings?: Partial<CollaborationSettings>
  ): CollaborationSession {
    if (!this.currentUser) {
      throw new Error('User not authenticated');
    }

    const session: CollaborationSession = {
      id: `session-${Date.now()}`,
      chartId,
      title,
      description,
      owner: this.currentUser,
      participants: [this.currentUser],
      status: 'active',
      createdAt: new Date(),
      updatedAt: new Date(),
      settings: {
        allowEditing: true,
        allowCommenting: true,
        allowSharing: true,
        requireApproval: false,
        autoSave: true,
        versionControl: true,
        maxParticipants: 10,
        sessionTimeout: 3600000,
        ...settings
      }
    };

    this.sessions.set(session.id, session);
    this.logActivity(chartId, 'access', 'Created new collaboration session');
    
    return session;
  }

  /**
   * Join collaboration session
   */
  joinCollaborationSession(sessionId: string, user: CollaborationUser): boolean {
    const session = this.sessions.get(sessionId);
    if (!session) {
      throw new Error('Session not found');
    }

    if (session.participants.length >= session.settings.maxParticipants) {
      throw new Error('Session is full');
    }

    if (session.participants.find(p => p.id === user.id)) {
      return true; // Already a participant
    }

    session.participants.push(user);
    session.updatedAt = new Date();
    this.logActivity(session.chartId, 'access', `${user.name} joined the session`);
    
    return true;
  }

  /**
   * Leave collaboration session
   */
  leaveCollaborationSession(sessionId: string, userId: string): boolean {
    const session = this.sessions.get(sessionId);
    if (!session) {
      throw new Error('Session not found');
    }

    const participantIndex = session.participants.findIndex(p => p.id === userId);
    if (participantIndex === -1) {
      return false;
    }

    const participant = session.participants[participantIndex];
    session.participants.splice(participantIndex, 1);
    session.updatedAt = new Date();
    
    this.logActivity(session.chartId, 'access', `${participant.name} left the session`);

    // If no participants left, end the session
    if (session.participants.length === 0) {
      session.status = 'ended';
    }

    return true;
  }

  /**
   * Add comment to chart
   */
  addComment(
    chartId: string,
    content: string,
    position?: { x: number; y: number; element?: string },
    replyToId?: string
  ): Comment {
    if (!this.currentUser) {
      throw new Error('User not authenticated');
    }

    const comment: Comment = {
      id: `comment-${Date.now()}`,
      chartId,
      author: this.currentUser,
      content,
      position,
      replies: [],
      createdAt: new Date(),
      updatedAt: new Date(),
      status: 'active',
      tags: []
    };

    if (replyToId) {
      // Add as reply to existing comment
      const parentComment = this.findComment(chartId, replyToId);
      if (parentComment) {
        parentComment.replies.push(comment);
      }
    } else {
      // Add as new comment
      if (!this.comments.has(chartId)) {
        this.comments.set(chartId, []);
      }
      this.comments.get(chartId)!.push(comment);
    }

    this.logActivity(chartId, 'comment', 'Added new comment');
    return comment;
  }

  /**
   * Find comment by ID
   */
  private findComment(chartId: string, commentId: string): Comment | null {
    const chartComments = this.comments.get(chartId) || [];
    
    for (const comment of chartComments) {
      if (comment.id === commentId) {
        return comment;
      }
      // Check replies
      const reply = comment.replies.find(r => r.id === commentId);
      if (reply) {
        return reply;
      }
    }
    
    return null;
  }

  /**
   * Get comments for chart
   */
  getComments(chartId: string): Comment[] {
    return this.comments.get(chartId) || [];
  }

  /**
   * Update comment
   */
  updateComment(chartId: string, commentId: string, content: string): Comment | null {
    const comment = this.findComment(chartId, commentId);
    if (!comment) {
      return null;
    }

    if (comment.author.id !== this.currentUser?.id) {
      throw new Error('Not authorized to edit this comment');
    }

    comment.content = content;
    comment.updatedAt = new Date();
    this.logActivity(chartId, 'comment', 'Updated comment');
    
    return comment;
  }

  /**
   * Delete comment
   */
  deleteComment(chartId: string, commentId: string): boolean {
    const chartComments = this.comments.get(chartId) || [];
    const commentIndex = chartComments.findIndex(c => c.id === commentId);
    
    if (commentIndex === -1) {
      return false;
    }

    const comment = chartComments[commentIndex];
    if (comment.author.id !== this.currentUser?.id) {
      throw new Error('Not authorized to delete this comment');
    }

    chartComments.splice(commentIndex, 1);
    this.logActivity(chartId, 'comment', 'Deleted comment');
    
    return true;
  }

  /**
   * Create share link
   */
  createShareLink(
    chartId: string,
    permissions: string[],
    expiresAt?: Date,
    maxViews?: number,
    password?: string
  ): ShareLink {
    if (!this.currentUser) {
      throw new Error('User not authenticated');
    }

    const shareLink: ShareLink = {
      id: `share-${Date.now()}`,
      chartId,
      url: `${window.location.origin}/share/${chartId}/${Date.now()}`,
      password,
      expiresAt,
      maxViews,
      currentViews: 0,
      permissions,
      createdAt: new Date(),
      createdBy: this.currentUser
    };

    this.shareLinks.set(shareLink.id, shareLink);
    this.logActivity(chartId, 'share', 'Created share link');
    
    return shareLink;
  }

  /**
   * Get share links for chart
   */
  getShareLinks(chartId: string): ShareLink[] {
    return Array.from(this.shareLinks.values()).filter(link => link.chartId === chartId);
  }

  /**
   * Revoke share link
   */
  revokeShareLink(shareLinkId: string): boolean {
    const shareLink = this.shareLinks.get(shareLinkId);
    if (!shareLink) {
      return false;
    }

    if (shareLink.createdBy.id !== this.currentUser?.id) {
      throw new Error('Not authorized to revoke this share link');
    }

    this.shareLinks.delete(shareLinkId);
    this.logActivity(shareLink.chartId, 'share', 'Revoked share link');
    
    return true;
  }

  /**
   * Create version history entry
   */
  createVersion(
    chartId: string,
    description: string,
    changes: string[],
    chartData: ChartData,
    chartConfig: ChartConfig
  ): VersionHistory {
    if (!this.currentUser) {
      throw new Error('User not authenticated');
    }

    if (!this.versionHistory.has(chartId)) {
      this.versionHistory.set(chartId, []);
    }

    const versions = this.versionHistory.get(chartId)!;
    const versionNumber = versions.length + 1;

    const version: VersionHistory = {
      id: `version-${Date.now()}`,
      chartId,
      version: versionNumber,
      description,
      changes,
      chartData,
      chartConfig,
      createdBy: this.currentUser,
      createdAt: new Date(),
      tags: []
    };

    versions.push(version);
    this.logActivity(chartId, 'version', `Created version ${versionNumber}`);
    
    return version;
  }

  /**
   * Get version history for chart
   */
  getVersionHistory(chartId: string): VersionHistory[] {
    return this.versionHistory.get(chartId) || [];
  }

  /**
   * Restore chart to specific version
   */
  restoreVersion(chartId: string, versionId: string): { chartData: ChartData; chartConfig: ChartConfig } | null {
    const versions = this.versionHistory.get(chartId) || [];
    const version = versions.find(v => v.id === versionId);
    
    if (!version) {
      return null;
    }

    this.logActivity(chartId, 'version', `Restored to version ${version.version}`);
    
    return {
      chartData: version.chartData,
      chartConfig: version.chartConfig
    };
  }

  /**
   * Send collaboration invite
   */
  sendInvite(
    chartId: string,
    email: string,
    role: 'editor' | 'viewer' | 'commenter',
    permissions: string[],
    message?: string
  ): CollaborationInvite {
    if (!this.currentUser) {
      throw new Error('User not authenticated');
    }

    const invite: CollaborationInvite = {
      id: `invite-${Date.now()}`,
      chartId,
      email,
      role,
      permissions,
      message,
      expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000), // 7 days
      status: 'pending',
      createdAt: new Date(),
      createdBy: this.currentUser
    };

    if (!this.invites.has(chartId)) {
      this.invites.set(chartId, []);
    }
    this.invites.get(chartId)!.push(invite);

    this.logActivity(chartId, 'permission', `Sent invite to ${email}`);
    
    return invite;
  }

  /**
   * Get invites for chart
   */
  getInvites(chartId: string): CollaborationInvite[] {
    return this.invites.get(chartId) || [];
  }

  /**
   * Accept collaboration invite
   */
  acceptInvite(inviteId: string): boolean {
    // Find invite across all charts
    for (const [chartId, invites] of this.invites.entries()) {
      const invite = invites.find(i => i.id === inviteId);
      if (invite && invite.status === 'pending') {
        invite.status = 'accepted';
        this.logActivity(chartId, 'permission', 'Accepted collaboration invite');
        return true;
      }
    }
    
    return false;
  }

  /**
   * Decline collaboration invite
   */
  declineInvite(inviteId: string): boolean {
    // Find invite across all charts
    for (const [chartId, invites] of this.invites.entries()) {
      const invite = invites.find(i => i.id === inviteId);
      if (invite && invite.status === 'pending') {
        invite.status = 'declined';
        this.logActivity(chartId, 'permission', 'Declined collaboration invite');
        return true;
      }
    }
    
    return false;
  }

  /**
   * Log collaboration activity
   */
  private logActivity(
    chartId: string,
    type: CollaborationActivity['type'],
    description: string,
    metadata?: Record<string, any>
  ): void {
    if (!this.currentUser) return;

    const activity: CollaborationActivity = {
      id: `activity-${Date.now()}`,
      chartId,
      type,
      user: this.currentUser,
      description,
      metadata,
      timestamp: new Date()
    };

    if (!this.activities.has(chartId)) {
      this.activities.set(chartId, []);
    }
    this.activities.get(chartId)!.push(activity);
  }

  /**
   * Get collaboration activities for chart
   */
  getActivities(chartId: string, limit: number = 50): CollaborationActivity[] {
    const activities = this.activities.get(chartId) || [];
    return activities
      .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
      .slice(0, limit);
  }

  /**
   * Get collaboration sessions for chart
   */
  getCollaborationSessions(chartId: string): CollaborationSession[] {
    return Array.from(this.sessions.values()).filter(session => session.chartId === chartId);
  }

  /**
   * Update collaboration session settings
   */
  updateSessionSettings(
    sessionId: string,
    settings: Partial<CollaborationSettings>
  ): CollaborationSession | null {
    const session = this.sessions.get(sessionId);
    if (!session) {
      return null;
    }

    if (session.owner.id !== this.currentUser?.id) {
      throw new Error('Not authorized to update session settings');
    }

    session.settings = { ...session.settings, ...settings };
    session.updatedAt = new Date();
    this.logActivity(session.chartId, 'permission', 'Updated session settings');
    
    return session;
  }

  /**
   * End collaboration session
   */
  endCollaborationSession(sessionId: string): boolean {
    const session = this.sessions.get(sessionId);
    if (!session) {
      return false;
    }

    if (session.owner.id !== this.currentUser?.id) {
      throw new Error('Not authorized to end session');
    }

    session.status = 'ended';
    session.updatedAt = new Date();
    this.logActivity(session.chartId, 'access', 'Ended collaboration session');
    
    return true;
  }

  /**
   * Check user permissions for chart
   */
  checkPermissions(chartId: string, requiredPermissions: string[]): boolean {
    if (!this.currentUser) {
      return false;
    }

    // Owner has all permissions
    const session = Array.from(this.sessions.values()).find(s => s.chartId === chartId);
    if (session?.owner.id === this.currentUser.id) {
      return true;
    }

    // Check participant permissions
    const participant = session?.participants.find(p => p.id === this.currentUser?.id);
    if (participant) {
      return requiredPermissions.every(permission => 
        participant.permissions.includes(permission)
      );
    }

    return false;
  }

  /**
   * Get collaboration statistics
   */
  getCollaborationStats(chartId: string): {
    totalParticipants: number;
    totalComments: number;
    totalVersions: number;
    totalShareLinks: number;
    lastActivity: Date | null;
  } {
    const sessions = this.getCollaborationSessions(chartId);
    const comments = this.getComments(chartId);
    const versions = this.getVersionHistory(chartId);
    const shareLinks = this.getShareLinks(chartId);
    const activities = this.getActivities(chartId, 1);

    return {
      totalParticipants: sessions.reduce((sum, s) => sum + s.participants.length, 0),
      totalComments: comments.length + comments.reduce((sum, c) => sum + c.replies.length, 0),
      totalVersions: versions.length,
      totalShareLinks: shareLinks.length,
      lastActivity: activities[0]?.timestamp || null
    };
  }
}

export const collaborationService = new CollaborationService();
export default collaborationService;
