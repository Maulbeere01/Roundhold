from typing import List, Protocol

class AnimatedObject(Protocol):
    """Protocol for all animated objects.
    
    Any object that implements update_animation() can be registered
    with the AnimationManager for centralized animation handling.
    """
    
    def update_animation(self, dt: float) -> None:
        """Update the animation state of this object.
        
        Args:
            dt: Delta time in seconds since last frame
        """
        ...


class AnimationManager:
    """Central manager for all animations.
    
    Manages all animated objects and updates them centrally.
    Simple to extend: Just register new animated objects.
    """
    
    def __init__(self):
        self.animated_objects: List[AnimatedObject] = []
    
    def register(self, obj: AnimatedObject) -> None:
        """Register an animated object.
        
        Args:
            obj: Animated object, must implement update_animation()
        """
        self.animated_objects.append(obj)
    
    def unregister(self, obj: AnimatedObject) -> None:
        """Unregister an animated object
        
        Args:
            obj: Animated object to remove from updates
        """
        if obj in self.animated_objects:
            self.animated_objects.remove(obj)
    
    def update_all(self, dt: float) -> None:
        """Update all animations.
        
        Args:
            dt: Delta time in seconds since last frame
        """
        for obj in self.animated_objects:
            obj.update_animation(dt)

