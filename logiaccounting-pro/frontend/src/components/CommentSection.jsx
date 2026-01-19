import { useState, useEffect } from 'react';
import { commentsAPI } from '../services/api';

export default function CommentSection({ entityType, entityId }) {
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newComment, setNewComment] = useState('');
  const [replyTo, setReplyTo] = useState(null);
  const [reactions, setReactions] = useState([]);

  useEffect(() => {
    loadComments();
    loadReactions();
  }, [entityType, entityId]);

  const loadComments = async () => {
    setLoading(true);
    try {
      const res = await commentsAPI.getEntityComments(entityType, entityId);
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

  const handleSubmit = async () => {
    if (!newComment.trim()) return;

    try {
      await commentsAPI.create({
        entity_type: entityType,
        entity_id: entityId,
        content: newComment,
        thread_id: replyTo?.id || null
      });
      setNewComment('');
      setReplyTo(null);
      loadComments();
    } catch (err) {
      alert('Failed to post comment');
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

  const handleDelete = async (commentId) => {
    if (!confirm('Delete this comment?')) return;
    try {
      await commentsAPI.delete(commentId);
      loadComments();
    } catch (err) {
      alert('Failed to delete');
    }
  };

  const renderComment = (comment, isReply = false) => (
    <div key={comment.id} className={`comment ${isReply ? 'reply' : ''}`}>
      <div className="comment-header">
        <span className="comment-author">{comment.author_name}</span>
        <span className="comment-date">
          {new Date(comment.created_at).toLocaleString()}
          {comment.is_edited && <span className="edited">(edited)</span>}
        </span>
      </div>
      <div className="comment-content">{comment.content}</div>

      {/* Reactions */}
      <div className="comment-reactions">
        {Object.entries(comment.reactions || {}).map(([emoji, users]) => (
          users.length > 0 && (
            <span key={emoji} className="reaction-badge">
              {emoji} {users.length}
            </span>
          )
        ))}
        <div className="add-reaction">
          {reactions.map(r => (
            <button
              key={r}
              className="reaction-btn"
              onClick={() => handleReaction(comment.id, r)}
            >
              {r}
            </button>
          ))}
        </div>
      </div>

      {/* Actions */}
      <div className="comment-actions">
        {!isReply && (
          <button
            className="btn-link"
            onClick={() => setReplyTo(comment)}
          >
            Reply
          </button>
        )}
        <button
          className="btn-link danger"
          onClick={() => handleDelete(comment.id)}
        >
          Delete
        </button>
      </div>

      {/* Replies */}
      {comment.replies?.length > 0 && (
        <div className="comment-replies">
          {comment.replies.map(reply => renderComment(reply, true))}
        </div>
      )}
    </div>
  );

  return (
    <div className="comment-section">
      <h4>Comments ({comments.length})</h4>

      {loading ? (
        <div className="text-center p-4">Loading...</div>
      ) : (
        <div className="comments-list">
          {comments.length === 0 ? (
            <div className="text-muted text-center p-4">No comments yet</div>
          ) : (
            comments.map(comment => renderComment(comment))
          )}
        </div>
      )}

      {/* New Comment Form */}
      <div className="comment-form">
        {replyTo && (
          <div className="reply-indicator">
            Replying to {replyTo.author_name}
            <button onClick={() => setReplyTo(null)}>x</button>
          </div>
        )}
        <textarea
          className="form-input"
          placeholder="Write a comment... Use @username to mention"
          value={newComment}
          onChange={(e) => setNewComment(e.target.value)}
          rows={3}
        />
        <button
          className="btn btn-primary"
          onClick={handleSubmit}
          disabled={!newComment.trim()}
        >
          Post Comment
        </button>
      </div>
    </div>
  );
}
