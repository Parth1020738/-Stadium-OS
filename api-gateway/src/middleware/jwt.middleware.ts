import { Injectable, NestMiddleware, UnauthorizedException, ForbiddenException } from '@nestjs/common';
import { Request, Response, NextFunction } from 'express';
import * as jwt from 'jsonwebtoken';

@Injectable()
export class JwtMiddleware implements NestMiddleware {
  use(req: Request, res: Response, next: NextFunction) {
    // Check for public routes
    if (req.path === '/health' || req.path.startsWith('/api/v1/auth/login') || req.path.startsWith('/api/v1/auth/register')) {
      return next();
    }

    const authHeader = req.headers.authorization;
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      throw new UnauthorizedException('Authorization header is missing or malformed');
    }

    const token = authHeader.split(' ')[1];
    try {
      const secret = process.env.JWT_SECRET || 'super-secure-jwt-secret-key-32-chars-long';
      const decoded = jwt.verify(token, secret);
      req['user'] = decoded;
      next();
    } catch (err) {
      throw new UnauthorizedException('Token validation failed: ' + err.message);
    }
  }
}
