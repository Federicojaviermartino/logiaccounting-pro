# LogiAccounting Pro - Phase 7 Tasks (Part 2/3)

## TEAM COLLABORATION + TAX MANAGEMENT + CUSTOM FIELDS

---

## TASK 4: TEAM COLLABORATION 👥

### 4.1 Create Collaboration Service

**File:** `backend/app/services/collaboration_service.py`

```python
"""
Team Collaboration Service
Comments, mentions, tasks, reactions
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import re
from app.models.store import db


class CollaborationService:
    """Manages comments, tasks, and mentions"""
    
    _instance = None
    _comments: Dict[str, dict] = {}
    _tasks: Dict[str, dict] = {}
    _comment_counter = 0
    _task_counter = 0
    
    REACTIONS = ["👍", "👎", "✅", "❌", "❓", "🎉", "❤️", "👀"]
    
    TASK_STATUSES = ["pending", "in_progress", "completed", "cancelled"]
    TASK_PRIORITIES = ["low", "medium", "high", "urgent"]
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._comments = {}
            cls._tasks = {}
            cls._comment_counter = 0
            cls._task_counter = 0
        return cls._instance
    
    # ========== COMMENTS ==========
    
    def create_comment(
        self,
        entity_type: str,
        entity_id: str,
        content: str,
        author_id: str,
        author_name: str,
        author_email: str,
        attachments: List[str] = None,
        thread_id: str = None
    ) -> dict:
        """Create a new comment"""
        self._comment_counter += 1
        comment_id = f"CMT-{self._comment_counter:05d}"
        
        # Extract mentions from content
        mentions = self._extract_mentions(content)
        
        comment = {
            "id": comment_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "content": content,
            "mentions": mentions,
            "author_id": author_id,
            "author_name": author_name,
            "author_email": author_email,
            "attachments": attachments or [],
            "reactions": {},
            "thread_id": thread_id,
            "replies_count": 0,
            "is_edited": False,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        self._comments[comment_id] = comment
        
        # Update parent's reply count if this is a reply
        if thread_id and thread_id in self._comments:
            self._comments[thread_id]["replies_count"] += 1
        
        return comment
    
    def _extract_mentions(self, content: str) -> List[str]:
        """Extract @mentions from content"""
        # Match @username or @email patterns
        pattern = r'@(\w+(?:@[\w.-]+)?)'
        matches = re.findall(pattern, content)
        return list(set(matches))
    
    def update_comment(self, comment_id: str, content: str) -> Optional[dict]:
        """Update comment content"""
        if comment_id not in self._comments:
            return None
        
        comment = self._comments[comment_id]
        comment["content"] = content
        comment["mentions"] = self._extract_mentions(content)
        comment["is_edited"] = True
        comment["updated_at"] = datetime.utcnow().isoformat()
        
        return comment
    
    def delete_comment(self, comment_id: str) -> bool:
        """Delete a comment"""
        if comment_id not in self._comments:
            return False
        
        comment = self._comments[comment_id]
        
        # Update parent's reply count
        if comment.get("thread_id") and comment["thread_id"] in self._comments:
            self._comments[comment["thread_id"]]["replies_count"] -= 1
        
        # Delete all replies if this is a parent
        if not comment.get("thread_id"):
            for c in list(self._comments.values()):
                if c.get("thread_id") == comment_id:
                    del self._comments[c["id"]]
        
        del self._comments[comment_id]
        return True
    
    def add_reaction(self, comment_id: str, reaction: str, user_id: str) -> Optional[dict]:
        """Add reaction to comment"""
        if comment_id not in self._comments:
            return None
        if reaction not in self.REACTIONS:
            return None
        
        comment = self._comments[comment_id]
        
        if reaction not in comment["reactions"]:
            comment["reactions"][reaction] = []
        
        if user_id not in comment["reactions"][reaction]:
            comment["reactions"][reaction].append(user_id)
        
        return comment
    
    def remove_reaction(self, comment_id: str, reaction: str, user_id: str) -> Optional[dict]:
        """Remove reaction from comment"""
        if comment_id not in self._comments:
            return None
        
        comment = self._comments[comment_id]
        
        if reaction in comment["reactions"] and user_id in comment["reactions"][reaction]:
            comment["reactions"][reaction].remove(user_id)
            if not comment["reactions"][reaction]:
                del comment["reactions"][reaction]
        
        return comment
    
    def get_comment(self, comment_id: str) -> Optional[dict]:
        """Get a comment"""
        return self._comments.get(comment_id)
    
    def get_entity_comments(self, entity_type: str, entity_id: str) -> List[dict]:
        """Get all comments for an entity"""
        comments = [
            c for c in self._comments.values()
            if c["entity_type"] == entity_type and c["entity_id"] == entity_id and not c.get("thread_id")
        ]
        
        # Add replies to each comment
        for comment in comments:
            comment["replies"] = sorted(
                [c for c in self._comments.values() if c.get("thread_id") == comment["id"]],
                key=lambda x: x["created_at"]
            )
        
        return sorted(comments, key=lambda x: x["created_at"], reverse=True)
    
    def get_user_mentions(self, user_id: str, user_email: str, unread_only: bool = False) -> List[dict]:
        """Get comments mentioning a user"""
        mentions = []
        search_terms = [user_id, user_email.split("@")[0], user_email]
        
        for comment in self._comments.values():
            for mention in comment.get("mentions", []):
                if any(term in mention.lower() for term in [t.lower() for t in search_terms if t]):
                    mentions.append(comment)
                    break
        
        return sorted(mentions, key=lambda x: x["created_at"], reverse=True)
    
    # ========== TASKS ==========
    
    def create_task(
        self,
        title: str,
        entity_type: str,
        entity_id: str,
        assigned_to: str,
        assigned_by: str,
        due_date: str = None,
        priority: str = "medium",
        notes: str = ""
    ) -> dict:
        """Create a new task"""
        self._task_counter += 1
        task_id = f"TASK-{self._task_counter:05d}"
        
        task = {
            "id": task_id,
            "title": title,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "assigned_to": assigned_to,
            "assigned_by": assigned_by,
            "due_date": due_date,
            "priority": priority,
            "status": "pending",
            "notes": notes,
            "completed_at": None,
            "created_at": datetime.utcnow().isoformat()
        }
        
        self._tasks[task_id] = task
        return task
    
    def update_task(self, task_id: str, updates: dict) -> Optional[dict]:
        """Update a task"""
        if task_id not in self._tasks:
            return None
        
        task = self._tasks[task_id]
        
        for key, value in updates.items():
            if key in task and key not in ["id", "created_at"]:
                task[key] = value
        
        # Set completed_at when status changes to completed
        if updates.get("status") == "completed" and not task["completed_at"]:
            task["completed_at"] = datetime.utcnow().isoformat()
        
        return task
    
    def delete_task(self, task_id: str) -> bool:
        """Delete a task"""
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False
    
    def get_task(self, task_id: str) -> Optional[dict]:
        """Get a task"""
        return self._tasks.get(task_id)
    
    def get_user_tasks(
        self,
        user_id: str,
        status: str = None,
        include_assigned_by: bool = False
    ) -> List[dict]:
        """Get tasks for a user"""
        tasks = []
        
        for task in self._tasks.values():
            if task["assigned_to"] == user_id:
                tasks.append(task)
            elif include_assigned_by and task["assigned_by"] == user_id:
                tasks.append(task)
        
        if status:
            tasks = [t for t in tasks if t["status"] == status]
        
        return sorted(tasks, key=lambda x: (x.get("due_date") or "9999", x["created_at"]))
    
    def get_entity_tasks(self, entity_type: str, entity_id: str) -> List[dict]:
        """Get tasks for an entity"""
        return sorted(
            [t for t in self._tasks.values() if t["entity_type"] == entity_type and t["entity_id"] == entity_id],
            key=lambda x: x["created_at"],
            reverse=True
        )
    
    def get_overdue_tasks(self) -> List[dict]:
        """Get all overdue tasks"""
        today = datetime.utcnow().date().isoformat()
        return [
            t for t in self._tasks.values()
            if t["status"] not in ["completed", "cancelled"]
            and t.get("due_date")
            and t["due_date"] < today
        ]
    
    def get_activity_feed(self, entity_type: str, entity_id: str, limit: int = 20) -> List[dict]:
        """Get combined activity feed for an entity"""
        activities = []
        
        # Add comments
        for comment in self._comments.values():
            if comment["entity_type"] == entity_type and comment["entity_id"] == entity_id:
                activities.append({
                    "type": "comment",
                    "data": comment,
                    "timestamp": comment["created_at"]
                })
        
        # Add tasks
        for task in self._tasks.values():
            if task["entity_type"] == entity_type and task["entity_id"] == entity_id:
                activities.append({
                    "type": "task",
                    "data": task,
                    "timestamp": task["created_at"]
                })
        
        return sorted(activities, key=lambda x: x["timestamp"], reverse=True)[:limit]


collaboration_service = CollaborationService()
```

### 4.2 Create Collaboration Routes

**File:** `backend/app/routes/comments.py`

```python
"""
Comments and Collaboration routes
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.collaboration_service import collaboration_service
from app.utils.auth import get_current_user

router = APIRouter()


class CreateCommentRequest(BaseModel):
    entity_type: str
    entity_id: str
    content: str
    attachments: List[str] = []
    thread_id: Optional[str] = None


class UpdateCommentRequest(BaseModel):
    content: str


class ReactionRequest(BaseModel):
    reaction: str


@router.get("/reactions")
async def get_available_reactions():
    """Get available reactions"""
    return {"reactions": collaboration_service.REACTIONS}


@router.post("")
async def create_comment(
    request: CreateCommentRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a comment"""
    return collaboration_service.create_comment(
        entity_type=request.entity_type,
        entity_id=request.entity_id,
        content=request.content,
        author_id=current_user["id"],
        author_name=current_user.get("name", current_user["email"]),
        author_email=current_user["email"],
        attachments=request.attachments,
        thread_id=request.thread_id
    )


@router.get("/entity/{entity_type}/{entity_id}")
async def get_entity_comments(
    entity_type: str,
    entity_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get comments for an entity"""
    return {"comments": collaboration_service.get_entity_comments(entity_type, entity_id)}


@router.get("/mentions")
async def get_my_mentions(current_user: dict = Depends(get_current_user)):
    """Get comments mentioning current user"""
    return {"mentions": collaboration_service.get_user_mentions(
        current_user["id"],
        current_user["email"]
    )}


@router.get("/{comment_id}")
async def get_comment(
    comment_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a comment"""
    comment = collaboration_service.get_comment(comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    return comment


@router.put("/{comment_id}")
async def update_comment(
    comment_id: str,
    request: UpdateCommentRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update a comment"""
    comment = collaboration_service.get_comment(comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment["author_id"] != current_user["id"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Cannot edit others' comments")
    
    updated = collaboration_service.update_comment(comment_id, request.content)
    return updated


@router.delete("/{comment_id}")
async def delete_comment(
    comment_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a comment"""
    comment = collaboration_service.get_comment(comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment["author_id"] != current_user["id"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Cannot delete others' comments")
    
    collaboration_service.delete_comment(comment_id)
    return {"message": "Comment deleted"}


@router.post("/{comment_id}/reactions")
async def add_reaction(
    comment_id: str,
    request: ReactionRequest,
    current_user: dict = Depends(get_current_user)
):
    """Add reaction to comment"""
    comment = collaboration_service.add_reaction(comment_id, request.reaction, current_user["id"])
    if not comment:
        raise HTTPException(status_code=400, detail="Invalid comment or reaction")
    return comment


@router.delete("/{comment_id}/reactions/{reaction}")
async def remove_reaction(
    comment_id: str,
    reaction: str,
    current_user: dict = Depends(get_current_user)
):
    """Remove reaction from comment"""
    comment = collaboration_service.remove_reaction(comment_id, reaction, current_user["id"])
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    return comment
```

**File:** `backend/app/routes/tasks.py`

```python
"""
Task Management routes
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.collaboration_service import collaboration_service
from app.utils.auth import get_current_user

router = APIRouter()


class CreateTaskRequest(BaseModel):
    title: str
    entity_type: str
    entity_id: str
    assigned_to: str
    due_date: Optional[str] = None
    priority: str = "medium"
    notes: str = ""


class UpdateTaskRequest(BaseModel):
    title: Optional[str] = None
    assigned_to: Optional[str] = None
    due_date: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


@router.get("/statuses")
async def get_statuses():
    """Get task statuses"""
    return {"statuses": collaboration_service.TASK_STATUSES}


@router.get("/priorities")
async def get_priorities():
    """Get task priorities"""
    return {"priorities": collaboration_service.TASK_PRIORITIES}


@router.get("/my")
async def get_my_tasks(
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get current user's tasks"""
    return {"tasks": collaboration_service.get_user_tasks(current_user["id"], status)}


@router.get("/overdue")
async def get_overdue_tasks(current_user: dict = Depends(get_current_user)):
    """Get all overdue tasks"""
    return {"tasks": collaboration_service.get_overdue_tasks()}


@router.post("")
async def create_task(
    request: CreateTaskRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a task"""
    return collaboration_service.create_task(
        title=request.title,
        entity_type=request.entity_type,
        entity_id=request.entity_id,
        assigned_to=request.assigned_to,
        assigned_by=current_user["id"],
        due_date=request.due_date,
        priority=request.priority,
        notes=request.notes
    )


@router.get("/entity/{entity_type}/{entity_id}")
async def get_entity_tasks(
    entity_type: str,
    entity_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get tasks for an entity"""
    return {"tasks": collaboration_service.get_entity_tasks(entity_type, entity_id)}


@router.get("/activity/{entity_type}/{entity_id}")
async def get_activity_feed(
    entity_type: str,
    entity_id: str,
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """Get activity feed for an entity"""
    return {"activities": collaboration_service.get_activity_feed(entity_type, entity_id, limit)}


@router.get("/{task_id}")
async def get_task(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a task"""
    task = collaboration_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/{task_id}")
async def update_task(
    task_id: str,
    request: UpdateTaskRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update a task"""
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    task = collaboration_service.update_task(task_id, updates)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a task"""
    if collaboration_service.delete_task(task_id):
        return {"message": "Task deleted"}
    raise HTTPException(status_code=404, detail="Task not found")
```

### 4.3 Add Collaboration API to Frontend

**Add to:** `frontend/src/services/api.js`

```javascript
// Comments API
export const commentsAPI = {
  getReactions: () => api.get('/api/v1/comments/reactions'),
  create: (data) => api.post('/api/v1/comments', data),
  getForEntity: (entityType, entityId) => api.get(`/api/v1/comments/entity/${entityType}/${entityId}`),
  getMentions: () => api.get('/api/v1/comments/mentions'),
  get: (commentId) => api.get(`/api/v1/comments/${commentId}`),
  update: (commentId, content) => api.put(`/api/v1/comments/${commentId}`, { content }),
  delete: (commentId) => api.delete(`/api/v1/comments/${commentId}`),
  addReaction: (commentId, reaction) => api.post(`/api/v1/comments/${commentId}/reactions`, { reaction }),
  removeReaction: (commentId, reaction) => api.delete(`/api/v1/comments/${commentId}/reactions/${reaction}`)
};

// Tasks API
export const tasksAPI = {
  getStatuses: () => api.get('/api/v1/tasks/statuses'),
  getPriorities: () => api.get('/api/v1/tasks/priorities'),
  getMyTasks: (status) => api.get('/api/v1/tasks/my', { params: { status } }),
  getOverdue: () => api.get('/api/v1/tasks/overdue'),
  create: (data) => api.post('/api/v1/tasks', data),
  getForEntity: (entityType, entityId) => api.get(`/api/v1/tasks/entity/${entityType}/${entityId}`),
  getActivity: (entityType, entityId, limit = 20) => api.get(`/api/v1/tasks/activity/${entityType}/${entityId}`, { params: { limit } }),
  get: (taskId) => api.get(`/api/v1/tasks/${taskId}`),
  update: (taskId, data) => api.put(`/api/v1/tasks/${taskId}`, data),
  delete: (taskId) => api.delete(`/api/v1/tasks/${taskId}`)
};
```

### 4.4 Create CommentSection Component

**File:** `frontend/src/components/collaboration/CommentSection.jsx`

```jsx
import { useState, useEffect } from 'react';
import { commentsAPI } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';

export default function CommentSection({ entityType, entityId }) {
  const { user } = useAuth();
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [replyTo, setReplyTo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [reactions, setReactions] = useState([]);
  const [editingComment, setEditingComment] = useState(null);
  const [editContent, setEditContent] = useState('');

  useEffect(() => {
    loadComments();
    loadReactions();
  }, [entityType, entityId]);

  const loadComments = async () => {
    try {
      const res = await commentsAPI.getForEntity(entityType, entityId);
      setComments(res.data.comments);
    } catch (err) {
      console.error('Failed to load comments:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadReactions = async () => {
    try {
      const res = await commentsAPI.getReactions();
      setReactions(res.data.reactions);
    } catch (err) {
      console.error('Failed to load reactions:', err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!newComment.trim()) return;

    try {
      await commentsAPI.create({
        entity_type: entityType,
        entity_id: entityId,
        content: newComment,
        thread_id: replyTo
      });
      setNewComment('');
      setReplyTo(null);
      loadComments();
    } catch (err) {
      alert('Failed to post comment');
    }
  };

  const handleEdit = async (commentId) => {
    try {
      await commentsAPI.update(commentId, editContent);
      setEditingComment(null);
      setEditContent('');
      loadComments();
    } catch (err) {
      alert('Failed to edit comment');
    }
  };

  const handleDelete = async (commentId) => {
    if (!confirm('Delete this comment?')) return;
    try {
      await commentsAPI.delete(commentId);
      loadComments();
    } catch (err) {
      alert('Failed to delete comment');
    }
  };

  const handleReaction = async (commentId, reaction) => {
    try {
      await commentsAPI.addReaction(commentId, reaction);
      loadComments();
    } catch (err) {
      console.error('Failed to add reaction:', err);
    }
  };

  const formatContent = (content) => {
    // Highlight @mentions
    return content.replace(/@(\w+(?:@[\w.-]+)?)/g, '<span class="mention">@$1</span>');
  };

  const renderComment = (comment, isReply = false) => (
    <div key={comment.id} className={`comment ${isReply ? 'reply' : ''}`}>
      <div className="comment-header">
        <div className="comment-avatar">
          {comment.author_name?.charAt(0).toUpperCase() || '?'}
        </div>
        <div className="comment-meta">
          <div className="comment-author">{comment.author_name}</div>
          <div className="comment-time">
            {new Date(comment.created_at).toLocaleString()}
            {comment.is_edited && <span className="edited">(edited)</span>}
          </div>
        </div>
        {comment.author_id === user?.id && (
          <div className="comment-actions">
            <button 
              className="btn-icon"
              onClick={() => { setEditingComment(comment.id); setEditContent(comment.content); }}
            >
              ✏️
            </button>
            <button 
              className="btn-icon"
              onClick={() => handleDelete(comment.id)}
            >
              🗑️
            </button>
          </div>
        )}
      </div>

      {editingComment === comment.id ? (
        <div className="comment-edit">
          <textarea
            value={editContent}
            onChange={(e) => setEditContent(e.target.value)}
            className="form-input"
            rows={2}
          />
          <div className="flex gap-2 mt-2">
            <button className="btn btn-sm btn-primary" onClick={() => handleEdit(comment.id)}>
              Save
            </button>
            <button className="btn btn-sm btn-secondary" onClick={() => setEditingComment(null)}>
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <div 
          className="comment-content"
          dangerouslySetInnerHTML={{ __html: formatContent(comment.content) }}
        />
      )}

      <div className="comment-footer">
        <div className="comment-reactions">
          {reactions.slice(0, 5).map(r => (
            <button
              key={r}
              className={`reaction-btn ${comment.reactions?.[r]?.includes(user?.id) ? 'active' : ''}`}
              onClick={() => handleReaction(comment.id, r)}
            >
              {r} {comment.reactions?.[r]?.length || ''}
            </button>
          ))}
        </div>
        {!isReply && (
          <button 
            className="btn-link"
            onClick={() => setReplyTo(comment.id)}
          >
            Reply
          </button>
        )}
      </div>

      {/* Replies */}
      {comment.replies?.length > 0 && (
        <div className="comment-replies">
          {comment.replies.map(reply => renderComment(reply, true))}
        </div>
      )}

      {/* Reply form */}
      {replyTo === comment.id && (
        <form onSubmit={handleSubmit} className="reply-form">
          <textarea
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            placeholder="Write a reply..."
            className="form-input"
            rows={2}
          />
          <div className="flex gap-2 mt-2">
            <button type="submit" className="btn btn-sm btn-primary">Reply</button>
            <button type="button" className="btn btn-sm btn-secondary" onClick={() => setReplyTo(null)}>Cancel</button>
          </div>
        </form>
      )}
    </div>
  );

  return (
    <div className="comment-section">
      <h4 className="comment-section-title">
        💬 Comments ({comments.reduce((acc, c) => acc + 1 + (c.replies?.length || 0), 0)})
      </h4>

      {/* New comment form */}
      {!replyTo && (
        <form onSubmit={handleSubmit} className="new-comment-form">
          <textarea
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            placeholder="Write a comment... Use @username to mention someone"
            className="form-input"
            rows={3}
          />
          <button type="submit" className="btn btn-primary mt-2" disabled={!newComment.trim()}>
            Post Comment
          </button>
        </form>
      )}

      {/* Comments list */}
      {loading ? (
        <div className="text-muted text-center p-4">Loading comments...</div>
      ) : comments.length === 0 ? (
        <div className="text-muted text-center p-4">No comments yet</div>
      ) : (
        <div className="comments-list">
          {comments.map(comment => renderComment(comment))}
        </div>
      )}
    </div>
  );
}
```

### 4.5 Create TeamTasks Page

**File:** `frontend/src/pages/TeamTasks.jsx`

```jsx
import { useState, useEffect } from 'react';
import { tasksAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

export default function TeamTasks() {
  const { user } = useAuth();
  const [tasks, setTasks] = useState([]);
  const [overdueTasks, setOverdueTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [showNewTask, setShowNewTask] = useState(false);
  const [newTask, setNewTask] = useState({
    title: '',
    entity_type: '',
    entity_id: '',
    assigned_to: '',
    due_date: '',
    priority: 'medium',
    notes: ''
  });

  useEffect(() => {
    loadTasks();
    loadOverdue();
  }, [filter]);

  const loadTasks = async () => {
    try {
      const status = filter === 'all' ? null : filter;
      const res = await tasksAPI.getMyTasks(status);
      setTasks(res.data.tasks);
    } catch (err) {
      console.error('Failed to load tasks:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadOverdue = async () => {
    try {
      const res = await tasksAPI.getOverdue();
      setOverdueTasks(res.data.tasks);
    } catch (err) {
      console.error('Failed to load overdue tasks:', err);
    }
  };

  const handleCreateTask = async () => {
    try {
      await tasksAPI.create(newTask);
      setShowNewTask(false);
      setNewTask({ title: '', entity_type: '', entity_id: '', assigned_to: '', due_date: '', priority: 'medium', notes: '' });
      loadTasks();
    } catch (err) {
      alert('Failed to create task');
    }
  };

  const handleStatusChange = async (taskId, status) => {
    try {
      await tasksAPI.update(taskId, { status });
      loadTasks();
    } catch (err) {
      alert('Failed to update task');
    }
  };

  const getPriorityColor = (priority) => {
    const colors = { urgent: 'danger', high: 'warning', medium: 'info', low: 'gray' };
    return colors[priority] || 'gray';
  };

  const getStatusIcon = (status) => {
    const icons = { pending: '⏳', in_progress: '🔄', completed: '✅', cancelled: '❌' };
    return icons[status] || '📋';
  };

  return (
    <>
      <div className="info-banner mb-6">
        ✅ Manage team tasks and track progress across all entities.
      </div>

      {/* Overdue Alert */}
      {overdueTasks.length > 0 && (
        <div className="alert alert-danger mb-6">
          <strong>⚠️ {overdueTasks.length} Overdue Tasks</strong>
          <ul className="mt-2">
            {overdueTasks.slice(0, 3).map(t => (
              <li key={t.id}>{t.title} - Due: {t.due_date}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Filters */}
      <div className="section mb-6">
        <div className="flex justify-between items-center">
          <div className="flex gap-2">
            {['all', 'pending', 'in_progress', 'completed'].map(f => (
              <button
                key={f}
                className={`btn btn-sm ${filter === f ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setFilter(f)}
              >
                {f.replace('_', ' ').charAt(0).toUpperCase() + f.replace('_', ' ').slice(1)}
              </button>
            ))}
          </div>
          <button className="btn btn-primary" onClick={() => setShowNewTask(true)}>
            ➕ New Task
          </button>
        </div>
      </div>

      {/* Tasks List */}
      <div className="section">
        {loading ? (
          <div className="text-center text-muted">Loading...</div>
        ) : tasks.length === 0 ? (
          <div className="text-center text-muted">No tasks found</div>
        ) : (
          <div className="tasks-list">
            {tasks.map(task => (
              <div key={task.id} className={`task-card ${task.status === 'completed' ? 'completed' : ''}`}>
                <div className="task-header">
                  <div className="task-status">{getStatusIcon(task.status)}</div>
                  <div className="task-title">{task.title}</div>
                  <span className={`badge badge-${getPriorityColor(task.priority)}`}>
                    {task.priority}
                  </span>
                </div>
                
                <div className="task-meta">
                  <span>📁 {task.entity_type}/{task.entity_id}</span>
                  {task.due_date && (
                    <span className={task.due_date < new Date().toISOString().split('T')[0] ? 'overdue' : ''}>
                      📅 {task.due_date}
                    </span>
                  )}
                </div>

                {task.notes && (
                  <div className="task-notes">{task.notes}</div>
                )}

                <div className="task-actions">
                  <select
                    className="form-select form-select-sm"
                    value={task.status}
                    onChange={(e) => handleStatusChange(task.id, e.target.value)}
                  >
                    <option value="pending">Pending</option>
                    <option value="in_progress">In Progress</option>
                    <option value="completed">Completed</option>
                    <option value="cancelled">Cancelled</option>
                  </select>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* New Task Modal */}
      {showNewTask && (
        <div className="modal-overlay" onClick={() => setShowNewTask(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Create Task</h3>
              <button className="modal-close" onClick={() => setShowNewTask(false)}>×</button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label className="form-label">Title *</label>
                <input
                  type="text"
                  className="form-input"
                  value={newTask.title}
                  onChange={(e) => setNewTask({ ...newTask, title: e.target.value })}
                  placeholder="Review Q4 expenses"
                />
              </div>
              <div className="grid-2">
                <div className="form-group">
                  <label className="form-label">Entity Type</label>
                  <select
                    className="form-select"
                    value={newTask.entity_type}
                    onChange={(e) => setNewTask({ ...newTask, entity_type: e.target.value })}
                  >
                    <option value="">Select...</option>
                    <option value="transaction">Transaction</option>
                    <option value="payment">Payment</option>
                    <option value="project">Project</option>
                    <option value="material">Material</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Entity ID</label>
                  <input
                    type="text"
                    className="form-input"
                    value={newTask.entity_id}
                    onChange={(e) => setNewTask({ ...newTask, entity_id: e.target.value })}
                    placeholder="TXN-001"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Assign To</label>
                  <input
                    type="text"
                    className="form-input"
                    value={newTask.assigned_to}
                    onChange={(e) => setNewTask({ ...newTask, assigned_to: e.target.value })}
                    placeholder="User ID or email"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Due Date</label>
                  <input
                    type="date"
                    className="form-input"
                    value={newTask.due_date}
                    onChange={(e) => setNewTask({ ...newTask, due_date: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Priority</label>
                  <select
                    className="form-select"
                    value={newTask.priority}
                    onChange={(e) => setNewTask({ ...newTask, priority: e.target.value })}
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="urgent">Urgent</option>
                  </select>
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">Notes</label>
                <textarea
                  className="form-input"
                  value={newTask.notes}
                  onChange={(e) => setNewTask({ ...newTask, notes: e.target.value })}
                  rows={3}
                />
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowNewTask(false)}>Cancel</button>
              <button 
                className="btn btn-primary" 
                onClick={handleCreateTask}
                disabled={!newTask.title}
              >
                Create Task
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
```

### 4.6 Add Collaboration Styles

**Add to:** `frontend/src/index.css`

```css
/* Comments */
.comment-section {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid var(--border-color);
}

.comment-section-title {
  margin: 0 0 16px 0;
}

.new-comment-form {
  margin-bottom: 24px;
}

.comments-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.comment {
  padding: 16px;
  background: var(--bg-tertiary);
  border-radius: 8px;
}

.comment.reply {
  margin-left: 32px;
  margin-top: 12px;
  background: var(--bg-secondary);
}

.comment-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.comment-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--primary);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
}

.comment-meta {
  flex: 1;
}

.comment-author {
  font-weight: 600;
}

.comment-time {
  font-size: 0.8rem;
  color: var(--text-muted);
}

.comment-time .edited {
  margin-left: 8px;
  font-style: italic;
}

.comment-actions {
  display: flex;
  gap: 4px;
}

.btn-icon {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  opacity: 0.5;
  transition: opacity 0.2s;
}

.btn-icon:hover {
  opacity: 1;
}

.comment-content {
  margin-bottom: 12px;
  line-height: 1.5;
}

.comment-content .mention {
  color: var(--primary);
  font-weight: 500;
}

.comment-footer {
  display: flex;
  align-items: center;
  gap: 16px;
}

.comment-reactions {
  display: flex;
  gap: 4px;
}

.reaction-btn {
  padding: 4px 8px;
  border: 1px solid var(--border-color);
  border-radius: 12px;
  background: none;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.2s;
}

.reaction-btn:hover, .reaction-btn.active {
  background: var(--primary);
  color: white;
  border-color: var(--primary);
}

.btn-link {
  background: none;
  border: none;
  color: var(--primary);
  cursor: pointer;
  font-size: 0.85rem;
}

.reply-form {
  margin-top: 12px;
  margin-left: 48px;
}

/* Tasks */
.tasks-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.task-card {
  padding: 16px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--card-bg);
}

.task-card.completed {
  opacity: 0.6;
}

.task-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.task-status {
  font-size: 1.25rem;
}

.task-title {
  flex: 1;
  font-weight: 600;
}

.task-meta {
  display: flex;
  gap: 16px;
  font-size: 0.85rem;
  color: var(--text-muted);
  margin-bottom: 8px;
}

.task-meta .overdue {
  color: #ef4444;
}

.task-notes {
  font-size: 0.9rem;
  color: var(--text-muted);
  margin-bottom: 12px;
}

.task-actions {
  display: flex;
  gap: 8px;
}

.form-select-sm {
  padding: 4px 8px;
  font-size: 0.85rem;
}
```

---

## TASK 5: TAX MANAGEMENT 🧾

### 5.1 Create Tax Service

**File:** `backend/app/services/tax_service.py`

```python
"""
Tax Management Service
"""

from datetime import datetime
from typing import Dict, List, Optional
from decimal import Decimal, ROUND_HALF_UP
from app.models.store import db


class TaxService:
    """Manages tax rates and calculations"""
    
    _instance = None
    _taxes: Dict[str, dict] = {}
    _counter = 0
    
    TAX_TYPES = ["vat", "sales_tax", "withholding", "income", "custom"]
    
    DEFAULT_TAXES = [
        {"name": "IVA 21%", "code": "IVA21", "type": "vat", "rate": 21.0, "is_default": True},
        {"name": "IVA 10.5%", "code": "IVA105", "type": "vat", "rate": 10.5, "is_default": False},
        {"name": "IVA 27%", "code": "IVA27", "type": "vat", "rate": 27.0, "is_default": False},
        {"name": "Exempt", "code": "EXEMPT", "type": "vat", "rate": 0.0, "is_default": False}
    ]
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._taxes = {}
            cls._counter = 0
            cls._init_default_taxes()
        return cls._instance
    
    @classmethod
    def _init_default_taxes(cls):
        """Initialize default tax rates"""
        for i, tax in enumerate(cls.DEFAULT_TAXES):
            tax_id = f"TAX-{i+1:03d}"
            cls._taxes[tax_id] = {
                "id": tax_id,
                **tax,
                "applies_to": ["products", "services"],
                "exempt_categories": [],
                "regions": [],
                "is_compound": False,
                "active": True,
                "created_at": datetime.utcnow().isoformat()
            }
        cls._counter = len(cls.DEFAULT_TAXES)
    
    def create_tax(
        self,
        name: str,
        code: str,
        tax_type: str,
        rate: float,
        applies_to: List[str] = None,
        exempt_categories: List[str] = None,
        regions: List[str] = None,
        is_compound: bool = False,
        is_default: bool = False
    ) -> dict:
        """Create a new tax rate"""
        self._counter += 1
        tax_id = f"TAX-{self._counter:03d}"
        
        # If setting as default, unset other defaults of same type
        if is_default:
            for t in self._taxes.values():
                if t["type"] == tax_type:
                    t["is_default"] = False
        
        tax = {
            "id": tax_id,
            "name": name,
            "code": code.upper(),
            "type": tax_type,
            "rate": rate,
            "applies_to": applies_to or ["products", "services"],
            "exempt_categories": exempt_categories or [],
            "regions": regions or [],
            "is_compound": is_compound,
            "is_default": is_default,
            "active": True,
            "created_at": datetime.utcnow().isoformat()
        }
        
        self._taxes[tax_id] = tax
        return tax
    
    def update_tax(self, tax_id: str, updates: dict) -> Optional[dict]:
        """Update a tax rate"""
        if tax_id not in self._taxes:
            return None
        
        tax = self._taxes[tax_id]
        
        for key, value in updates.items():
            if key in tax and key not in ["id", "created_at"]:
                tax[key] = value
        
        return tax
    
    def delete_tax(self, tax_id: str) -> bool:
        """Delete a tax rate"""
        if tax_id in self._taxes:
            del self._taxes[tax_id]
            return True
        return False
    
    def get_tax(self, tax_id: str) -> Optional[dict]:
        """Get a tax rate"""
        return self._taxes.get(tax_id)
    
    def get_by_code(self, code: str) -> Optional[dict]:
        """Get tax by code"""
        for tax in self._taxes.values():
            if tax["code"] == code.upper():
                return tax
        return None
    
    def list_taxes(self, active_only: bool = True, tax_type: str = None) -> List[dict]:
        """List all tax rates"""
        taxes = list(self._taxes.values())
        
        if active_only:
            taxes = [t for t in taxes if t["active"]]
        
        if tax_type:
            taxes = [t for t in taxes if t["type"] == tax_type]
        
        return sorted(taxes, key=lambda x: (x["type"], x["rate"]))
    
    def get_default_tax(self, tax_type: str = "vat") -> Optional[dict]:
        """Get default tax for a type"""
        for tax in self._taxes.values():
            if tax["type"] == tax_type and tax["is_default"] and tax["active"]:
                return tax
        return None
    
    def calculate_tax(
        self,
        amount: float,
        tax_id: str = None,
        tax_code: str = None,
        is_inclusive: bool = False
    ) -> dict:
        """Calculate tax for an amount"""
        tax = None
        
        if tax_id:
            tax = self.get_tax(tax_id)
        elif tax_code:
            tax = self.get_by_code(tax_code)
        else:
            tax = self.get_default_tax()
        
        if not tax:
            return {
                "amount": amount,
                "tax_amount": 0,
                "total": amount,
                "tax_rate": 0,
                "tax_id": None
            }
        
        rate = tax["rate"] / 100
        
        if is_inclusive:
            # Tax is already included in amount
            base = amount / (1 + rate)
            tax_amount = amount - base
        else:
            # Tax is on top of amount
            base = amount
            tax_amount = amount * rate
        
        # Round to 2 decimal places
        base = round(base, 2)
        tax_amount = round(tax_amount, 2)
        total = round(base + tax_amount, 2)
        
        return {
            "base_amount": base,
            "tax_amount": tax_amount,
            "total": total,
            "tax_rate": tax["rate"],
            "tax_id": tax["id"],
            "tax_code": tax["code"],
            "tax_name": tax["name"]
        }
    
    def calculate_multiple_taxes(
        self,
        amount: float,
        tax_ids: List[str],
        is_compound: bool = False
    ) -> dict:
        """Calculate multiple taxes"""
        results = []
        total_tax = 0
        running_amount = amount
        
        for tax_id in tax_ids:
            tax = self.get_tax(tax_id)
            if not tax:
                continue
            
            base = running_amount if is_compound else amount
            tax_amount = round(base * (tax["rate"] / 100), 2)
            total_tax += tax_amount
            
            results.append({
                "tax_id": tax_id,
                "tax_code": tax["code"],
                "tax_name": tax["name"],
                "tax_rate": tax["rate"],
                "tax_amount": tax_amount
            })
            
            if is_compound:
                running_amount += tax_amount
        
        return {
            "base_amount": amount,
            "taxes": results,
            "total_tax": round(total_tax, 2),
            "total": round(amount + total_tax, 2),
            "is_compound": is_compound
        }
    
    def generate_tax_report(
        self,
        period_start: str,
        period_end: str
    ) -> dict:
        """Generate tax report for a period"""
        transactions = db.transactions.find_all()
        
        # Filter by period
        period_txns = [
            t for t in transactions
            if period_start <= t.get("date", "") <= period_end
        ]
        
        # Calculate collected taxes (sales/income)
        collected = {}
        for txn in period_txns:
            if txn.get("type") == "income" and txn.get("tax_id"):
                tax_id = txn["tax_id"]
                tax_amount = txn.get("tax_amount", 0)
                if tax_id not in collected:
                    tax = self.get_tax(tax_id)
                    collected[tax_id] = {
                        "tax_code": tax["code"] if tax else "Unknown",
                        "tax_name": tax["name"] if tax else "Unknown",
                        "amount": 0,
                        "count": 0
                    }
                collected[tax_id]["amount"] += tax_amount
                collected[tax_id]["count"] += 1
        
        # Calculate paid taxes (purchases/expenses)
        paid = {}
        for txn in period_txns:
            if txn.get("type") == "expense" and txn.get("tax_id"):
                tax_id = txn["tax_id"]
                tax_amount = txn.get("tax_amount", 0)
                if tax_id not in paid:
                    tax = self.get_tax(tax_id)
                    paid[tax_id] = {
                        "tax_code": tax["code"] if tax else "Unknown",
                        "tax_name": tax["name"] if tax else "Unknown",
                        "amount": 0,
                        "count": 0
                    }
                paid[tax_id]["amount"] += tax_amount
                paid[tax_id]["count"] += 1
        
        total_collected = sum(c["amount"] for c in collected.values())
        total_paid = sum(p["amount"] for p in paid.values())
        
        return {
            "period_start": period_start,
            "period_end": period_end,
            "collected": list(collected.values()),
            "total_collected": round(total_collected, 2),
            "paid": list(paid.values()),
            "total_paid": round(total_paid, 2),
            "net_liability": round(total_collected - total_paid, 2),
            "transaction_count": len(period_txns)
        }


tax_service = TaxService()
```

### 5.2 Create Tax Routes

**File:** `backend/app/routes/taxes.py`

```python
"""
Tax Management routes
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.tax_service import tax_service
from app.utils.auth import get_current_user, require_roles

router = APIRouter()


class CreateTaxRequest(BaseModel):
    name: str
    code: str
    type: str
    rate: float
    applies_to: List[str] = ["products", "services"]
    exempt_categories: List[str] = []
    regions: List[str] = []
    is_compound: bool = False
    is_default: bool = False


class UpdateTaxRequest(BaseModel):
    name: Optional[str] = None
    rate: Optional[float] = None
    applies_to: Optional[List[str]] = None
    exempt_categories: Optional[List[str]] = None
    is_default: Optional[bool] = None
    active: Optional[bool] = None


class CalculateTaxRequest(BaseModel):
    amount: float
    tax_id: Optional[str] = None
    tax_code: Optional[str] = None
    is_inclusive: bool = False


@router.get("/types")
async def get_tax_types():
    """Get available tax types"""
    return {"types": tax_service.TAX_TYPES}


@router.get("")
async def list_taxes(
    active_only: bool = True,
    tax_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """List all taxes"""
    return {"taxes": tax_service.list_taxes(active_only, tax_type)}


@router.post("")
async def create_tax(
    request: CreateTaxRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Create a tax rate"""
    return tax_service.create_tax(
        name=request.name,
        code=request.code,
        tax_type=request.type,
        rate=request.rate,
        applies_to=request.applies_to,
        exempt_categories=request.exempt_categories,
        regions=request.regions,
        is_compound=request.is_compound,
        is_default=request.is_default
    )


@router.get("/default")
async def get_default_tax(
    tax_type: str = "vat",
    current_user: dict = Depends(get_current_user)
):
    """Get default tax"""
    tax = tax_service.get_default_tax(tax_type)
    if not tax:
        raise HTTPException(status_code=404, detail="No default tax found")
    return tax


@router.post("/calculate")
async def calculate_tax(
    request: CalculateTaxRequest,
    current_user: dict = Depends(get_current_user)
):
    """Calculate tax for an amount"""
    return tax_service.calculate_tax(
        amount=request.amount,
        tax_id=request.tax_id,
        tax_code=request.tax_code,
        is_inclusive=request.is_inclusive
    )


@router.get("/report")
async def get_tax_report(
    period_start: str,
    period_end: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Generate tax report"""
    return tax_service.generate_tax_report(period_start, period_end)


@router.get("/{tax_id}")
async def get_tax(
    tax_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a tax rate"""
    tax = tax_service.get_tax(tax_id)
    if not tax:
        raise HTTPException(status_code=404, detail="Tax not found")
    return tax


@router.put("/{tax_id}")
async def update_tax(
    tax_id: str,
    request: UpdateTaxRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Update a tax rate"""
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    tax = tax_service.update_tax(tax_id, updates)
    if not tax:
        raise HTTPException(status_code=404, detail="Tax not found")
    return tax


@router.delete("/{tax_id}")
async def delete_tax(
    tax_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Delete a tax rate"""
    if tax_service.delete_tax(tax_id):
        return {"message": "Tax deleted"}
    raise HTTPException(status_code=404, detail="Tax not found")
```

### 5.3 Add Tax API & Create Page

**Add to:** `frontend/src/services/api.js`

```javascript
// Tax API
export const taxAPI = {
  getTypes: () => api.get('/api/v1/taxes/types'),
  list: (activeOnly = true, taxType) => api.get('/api/v1/taxes', { params: { active_only: activeOnly, tax_type: taxType } }),
  create: (data) => api.post('/api/v1/taxes', data),
  getDefault: (taxType = 'vat') => api.get('/api/v1/taxes/default', { params: { tax_type: taxType } }),
  calculate: (amount, taxId, taxCode, isInclusive = false) => 
    api.post('/api/v1/taxes/calculate', { amount, tax_id: taxId, tax_code: taxCode, is_inclusive: isInclusive }),
  getReport: (periodStart, periodEnd) => api.get('/api/v1/taxes/report', { params: { period_start: periodStart, period_end: periodEnd } }),
  get: (taxId) => api.get(`/api/v1/taxes/${taxId}`),
  update: (taxId, data) => api.put(`/api/v1/taxes/${taxId}`, data),
  delete: (taxId) => api.delete(`/api/v1/taxes/${taxId}`)
};
```

**File:** `frontend/src/pages/TaxManagement.jsx` (abbreviated for length)

```jsx
import { useState, useEffect } from 'react';
import { taxAPI } from '../services/api';

export default function TaxManagement() {
  const [taxes, setTaxes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [report, setReport] = useState(null);
  const [reportPeriod, setReportPeriod] = useState({
    start: new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0],
    end: new Date().toISOString().split('T')[0]
  });

  useEffect(() => {
    loadTaxes();
  }, []);

  const loadTaxes = async () => {
    try {
      const res = await taxAPI.list();
      setTaxes(res.data.taxes);
    } catch (err) {
      console.error('Failed to load taxes:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadReport = async () => {
    try {
      const res = await taxAPI.getReport(reportPeriod.start, reportPeriod.end);
      setReport(res.data);
    } catch (err) {
      alert('Failed to generate report');
    }
  };

  return (
    <>
      <div className="info-banner mb-6">
        🧾 Manage tax rates and generate tax reports for compliance.
      </div>

      {/* Tax Rates List */}
      <div className="section mb-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="section-title" style={{ margin: 0 }}>Tax Rates</h3>
          <button className="btn btn-primary" onClick={() => setShowForm(true)}>
            ➕ Add Tax Rate
          </button>
        </div>

        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Code</th>
                <th>Name</th>
                <th>Type</th>
                <th>Rate</th>
                <th>Default</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {taxes.map(tax => (
                <tr key={tax.id}>
                  <td><code>{tax.code}</code></td>
                  <td>{tax.name}</td>
                  <td>{tax.type}</td>
                  <td><strong>{tax.rate}%</strong></td>
                  <td>{tax.is_default ? '✅' : ''}</td>
                  <td>
                    <span className={`badge badge-${tax.active ? 'success' : 'gray'}`}>
                      {tax.active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Tax Report */}
      <div className="section">
        <h3 className="section-title">Tax Report</h3>
        <div className="flex gap-4 mb-4">
          <input
            type="date"
            className="form-input"
            value={reportPeriod.start}
            onChange={(e) => setReportPeriod({ ...reportPeriod, start: e.target.value })}
          />
          <input
            type="date"
            className="form-input"
            value={reportPeriod.end}
            onChange={(e) => setReportPeriod({ ...reportPeriod, end: e.target.value })}
          />
          <button className="btn btn-primary" onClick={loadReport}>
            Generate Report
          </button>
        </div>

        {report && (
          <div className="tax-report">
            <div className="report-row">
              <div className="report-section">
                <h4>Tax Collected (Sales)</h4>
                {report.collected.map((c, i) => (
                  <div key={i} className="report-line">
                    <span>{c.tax_name}</span>
                    <span>${c.amount.toLocaleString()}</span>
                  </div>
                ))}
                <div className="report-total">
                  <span>Total Collected</span>
                  <span>${report.total_collected.toLocaleString()}</span>
                </div>
              </div>

              <div className="report-section">
                <h4>Tax Paid (Purchases)</h4>
                {report.paid.map((p, i) => (
                  <div key={i} className="report-line">
                    <span>{p.tax_name}</span>
                    <span>${p.amount.toLocaleString()}</span>
                  </div>
                ))}
                <div className="report-total">
                  <span>Total Paid</span>
                  <span>${report.total_paid.toLocaleString()}</span>
                </div>
              </div>
            </div>

            <div className="report-summary">
              <div className="report-net">
                <span>Net Tax Liability</span>
                <span className={report.net_liability >= 0 ? 'positive' : 'negative'}>
                  ${Math.abs(report.net_liability).toLocaleString()}
                  {report.net_liability >= 0 ? ' (payable)' : ' (credit)'}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
```

---

## TASK 6: REGISTER ROUTES

### 6.1 Update Backend main.py

```python
from app.routes import comments, tasks, taxes

app.include_router(comments.router, prefix="/api/v1/comments", tags=["Comments"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["Tasks"])
app.include_router(taxes.router, prefix="/api/v1/taxes", tags=["Taxes"])
```

### 6.2 Update Frontend App.jsx

```jsx
const TeamTasks = lazy(() => import('./pages/TeamTasks'));
const TaxManagement = lazy(() => import('./pages/TaxManagement'));

<Route path="/tasks" element={
  <PrivateRoute><Layout><TeamTasks /></Layout></PrivateRoute>
} />
<Route path="/taxes" element={
  <PrivateRoute roles={['admin']}>
    <Layout><TaxManagement /></Layout>
  </PrivateRoute>
} />
```

---

## COMPLETION CHECKLIST - PART 2

### Team Collaboration
- [ ] Comments service (CRUD, mentions, reactions)
- [ ] Tasks service (CRUD, status, priority)
- [ ] Comments routes
- [ ] Tasks routes  
- [ ] CommentSection component
- [ ] TeamTasks page

### Tax Management
- [ ] Tax service (rates, calculation, reports)
- [ ] Tax routes
- [ ] Tax management page
- [ ] Tax report generation

---

**Continue to Part 3 for Custom Fields, Inventory Forecasting, Payment Gateway, E-commerce Sync, Advanced Analytics, and White-Label**
